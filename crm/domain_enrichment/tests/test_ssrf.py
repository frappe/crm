# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure unit tests for the SSRF guard (``http.validate_url`` / ``http._is_blocked_ip``).

These are fully offline: ``socket.getaddrinfo`` is monkeypatched so DNS resolution
is deterministic and no network call is ever made. The guard must reject loopback,
link-local, private and reserved addresses (incl. the cloud-metadata endpoint
169.254.169.254), reject non-http(s) schemes, honor allow/block domain lists, and
allow a normal public host — unless ``allow_private_networks`` is set.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest import mock

from frappe.tests import UnitTestCase

from crm.domain_enrichment import http
from crm.domain_enrichment.http import SSRFError, validate_url
from crm.domain_enrichment.tests.fixtures import make_config


@contextmanager
def _resolves_to(ip_map):
	"""Patch socket.getaddrinfo so a host resolves to the given IP(s).

	``ip_map`` maps hostname -> ip string (or list of ip strings). An unknown host
	raises gaierror, mimicking a real resolver failure.
	"""
	import socket

	def fake_getaddrinfo(host, *args, **kwargs):
		if host not in ip_map:
			raise socket.gaierror(f"unknown host {host}")
		ips = ip_map[host]
		if isinstance(ips, str):
			ips = [ips]
		# getaddrinfo returns 5-tuples; element 4 is the sockaddr (ip, port, ...).
		return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0)) for ip in ips]

	with mock.patch.object(http.socket, "getaddrinfo", side_effect=fake_getaddrinfo):
		yield


class SSRFGuardTest(UnitTestCase):
	def setUp(self):
		self.cfg = make_config()  # default: allow_private_networks falsy, no allow/block lists

	# -- rejection of internal / dangerous addresses ----------------------- #
	def test_rejects_loopback_127(self):
		with _resolves_to({"evil.example": "127.0.0.1"}):
			with self.assertRaises(SSRFError):
				validate_url("http://evil.example/", self.cfg)

	def test_rejects_cloud_metadata_link_local(self):
		# 169.254.169.254 is the AWS/GCP metadata endpoint — a classic SSRF target.
		with _resolves_to({"metadata.example": "169.254.169.254"}):
			with self.assertRaises(SSRFError):
				validate_url("http://metadata.example/latest/meta-data/", self.cfg)

	def test_rejects_private_10_range(self):
		with _resolves_to({"intranet.example": "10.0.0.5"}):
			with self.assertRaises(SSRFError):
				validate_url("http://intranet.example/", self.cfg)

	def test_rejects_localhost(self):
		with _resolves_to({"localhost": "127.0.0.1"}):
			with self.assertRaises(SSRFError):
				validate_url("http://localhost:8000/", self.cfg)

	def test_rejects_ipv6_loopback(self):
		with _resolves_to({"v6.example": "::1"}):
			with self.assertRaises(SSRFError):
				validate_url("http://v6.example/", self.cfg)

	# -- scheme validation ------------------------------------------------- #
	def test_rejects_non_http_scheme(self):
		with self.assertRaises(SSRFError):
			validate_url("ftp://example.com/x", self.cfg)
		with self.assertRaises(SSRFError):
			validate_url("file:///etc/passwd", self.cfg)
		with self.assertRaises(SSRFError):
			validate_url("gopher://example.com/", self.cfg)

	def test_rejects_url_without_host(self):
		with self.assertRaises(SSRFError):
			validate_url("http:///nohost", self.cfg)

	def test_rejects_unresolvable_host(self):
		with _resolves_to({}):  # nothing resolves
			with self.assertRaises(SSRFError):
				validate_url("http://does-not-resolve.example/", self.cfg)

	# -- the happy path ---------------------------------------------------- #
	def test_allows_public_host(self):
		with _resolves_to({"frappe.io": "104.21.0.1"}):
			self.assertEqual(validate_url("https://frappe.io/", self.cfg), "https://frappe.io/")

	def test_rejects_when_any_resolved_ip_is_private(self):
		# DNS-rebinding style: one public + one private IP -> must reject.
		with _resolves_to({"mixed.example": ["8.8.8.8", "10.1.2.3"]}):
			with self.assertRaises(SSRFError):
				validate_url("http://mixed.example/", self.cfg)

	# -- allow_private_networks bypass ------------------------------------- #
	def test_allow_private_networks_bypasses_ip_check(self):
		cfg = make_config(settings={"allow_private_networks": 1})
		# No DNS patch needed: the guard must not resolve at all when bypassed.
		self.assertEqual(validate_url("http://10.0.0.5/", cfg), "http://10.0.0.5/")
		self.assertEqual(validate_url("http://localhost:8000/", cfg), "http://localhost:8000/")

	# -- allow / block lists ----------------------------------------------- #
	def test_blocked_domain_is_always_rejected(self):
		cfg = make_config(blocked_domains=["evil.com"])
		with _resolves_to({"evil.com": "8.8.8.8"}):
			with self.assertRaises(SSRFError):
				validate_url("http://evil.com/", cfg)
		# Subdomains of a blocked domain are blocked too.
		with _resolves_to({"sub.evil.com": "8.8.8.8"}):
			with self.assertRaises(SSRFError):
				validate_url("http://sub.evil.com/", cfg)

	def test_allow_list_restricts_to_listed_hosts(self):
		cfg = make_config(allowed_domains=["good.com"])
		with _resolves_to({"good.com": "8.8.8.8", "other.com": "8.8.8.8"}):
			self.assertEqual(validate_url("http://good.com/", cfg), "http://good.com/")
			with self.assertRaises(SSRFError):
				validate_url("http://other.com/", cfg)

	# -- direct IP-classification unit ------------------------------------- #
	def test_is_blocked_ip_classification(self):
		for ip in ("127.0.0.1", "10.0.0.5", "172.16.0.1", "192.168.1.1", "169.254.169.254", "::1", "0.0.0.0"):
			self.assertTrue(http._is_blocked_ip(ip), ip)
		for ip in ("8.8.8.8", "104.21.0.1", "1.1.1.1"):
			self.assertFalse(http._is_blocked_ip(ip), ip)
		# Unparseable -> rejected.
		self.assertTrue(http._is_blocked_ip("not-an-ip"))
