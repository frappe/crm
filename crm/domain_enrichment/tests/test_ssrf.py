# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Pure unit tests for the SSRF guard (``http.validate_url`` / ``http._is_blocked_ip``).

These are fully offline: ``socket.getaddrinfo`` is monkeypatched so DNS resolution
is deterministic and no network call is ever made. The guard must reject loopback,
link-local, private and reserved addresses (incl. the cloud-metadata endpoint
169.254.169.254), reject non-http(s) schemes, honor allow/block domain lists, and
allow a normal public host. The private-network rejection is unconditional --
there is no setting to disable it.
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
		self.cfg = make_config()  # default: no allow/block lists

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

	# -- the private-network guard is unconditional ------------------------ #
	def test_private_network_guard_cannot_be_disabled(self):
		# There is no setting to allow private networks -- a would-be bypass flag
		# is inert, the guard still rejects a private address.
		cfg = make_config(settings={"allow_private_networks": 1})
		with _resolves_to({"intranet.example": "10.0.0.5"}):
			with self.assertRaises(SSRFError):
				validate_url("http://intranet.example/", cfg)

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


class PinnedConnectionTest(UnitTestCase):
	"""DNS-rebinding defense: the socket must go to the IP the guard validated.

	``_pinned_get`` rewrites the URL netloc to the validated IP and keeps the
	original hostname in the Host header / TLS SNI, so a resolver answer that
	changes after validation can no longer steer the connection.
	"""

	def _capture_send(self, captured):
		import requests

		def fake_send(adapter, request, **kwargs):
			captured["url"] = request.url
			captured["host_header"] = request.headers.get("Host")
			raise requests.exceptions.ConnectionError("offline test: no socket")

		return mock.patch.object(http._PinnedIPAdapter, "send", autospec=True, side_effect=fake_send)

	def test_pinned_get_connects_to_ip_with_hostname_host_header(self):
		import requests

		captured = {}
		with self._capture_send(captured), self.assertRaises(requests.exceptions.ConnectionError):
			http._pinned_get(requests.Session(), "https://example.com/about", "93.184.216.34", 5, 2)
		self.assertEqual(captured["url"], "https://93.184.216.34/about")
		self.assertEqual(captured["host_header"], "example.com")

	def test_pinned_get_brackets_ipv6_and_keeps_explicit_port(self):
		import requests

		captured = {}
		with self._capture_send(captured), self.assertRaises(requests.exceptions.ConnectionError):
			http._pinned_get(requests.Session(), "https://example.com:8443/x", "2606:2800:220:1::", 5, 2)
		self.assertEqual(captured["url"], "https://[2606:2800:220:1::]:8443/x")
		self.assertEqual(captured["host_header"], "example.com:8443")

	def test_pinned_adapter_keeps_tls_verification_on_hostname(self):
		adapter = http._PinnedIPAdapter("example.com")
		# urllib3 uses server_hostname for SNI and falls back to it for certificate
		# matching, so verification stays against the hostname, not the IP literal.
		self.assertEqual(adapter.poolmanager.connection_pool_kw.get("server_hostname"), "example.com")

	def test_fetch_connects_to_the_validated_ip(self):
		import requests

		captured = {}
		with _resolves_to({"rebind.example": "8.8.8.8"}), self._capture_send(captured):
			status, _html, error, _final = http.fetch("http://rebind.example/", make_config())
		self.assertEqual(captured["url"], "http://8.8.8.8/")
		self.assertEqual(status, 0)
		self.assertIn("connection error", error)
