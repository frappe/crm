# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for the registry HTTP client (no framework state, no network).

The ``requests`` session is replaced with a fake so every branch of ``fetch`` is
exercised offline: a 200 success, document/account error codes, a timeout, an invalid
JSON body, a body over the size cap, and an unfollowed redirect. The token-masking
helper is checked directly and through a transport-error log.
"""

from __future__ import annotations

import json
from unittest import mock

import requests
from frappe.tests import UnitTestCase

from crm.registry_enrichment import client

TOKEN = "5ae973d7a997af13f0aaf2bf60e65803"


class _FakeResponse:
	def __init__(self, status_code=200, body=b"", chunks=None):
		self.status_code = status_code
		self._chunks = chunks if chunks is not None else [body]
		self.closed = False

	def iter_content(self, chunk_size=16_384, decode_unicode=False):
		yield from self._chunks

	def close(self):
		self.closed = True


class _FakeSession:
	def __init__(self, response=None, exc=None):
		self._response = response
		self._exc = exc
		self.get_kwargs = None

	def get(self, url, **kwargs):
		self.get_kwargs = kwargs
		if self._exc is not None:
			raise self._exc
		return self._response


def _json_body(payload: dict) -> bytes:
	return json.dumps(payload).encode("utf-8")


def _patch_session(session):
	return mock.patch.object(client, "_session", return_value=session)


class MaskTest(UnitTestCase):
	def test_masks_token(self):
		text = f"https://api.cpfcnpj.com.br/{TOKEN}/6/12345678000195"
		self.assertNotIn(TOKEN, client._mask(text, TOKEN))
		self.assertIn("***", client._mask(text, TOKEN))

	def test_no_token_is_a_noop(self):
		self.assertEqual(client._mask("plain text", ""), "plain text")


class FetchTest(UnitTestCase):
	def test_success_returns_payload(self):
		payload = {"status": 1, "cnpj": "12.345.678/0001-95", "razao": "TOKEN TEST LTDA"}
		session = _FakeSession(_FakeResponse(200, _json_body(payload)))
		with _patch_session(session):
			result = client.fetch("12345678000195", 6, TOKEN, timeout=15)
		self.assertEqual(result["razao"], "TOKEN TEST LTDA")
		# Redirects are not followed and the body is streamed.
		self.assertIs(session.get_kwargs["allow_redirects"], False)
		self.assertIs(session.get_kwargs["stream"], True)

	def test_document_error_code(self):
		body = {"status": 0, "erroCodigo": 200, "erro": "CNPJ invalido"}
		session = _FakeSession(_FakeResponse(400, _json_body(body)))
		with _patch_session(session):
			with self.assertRaises(client.RegistryLookupError) as ctx:
				client.fetch("12345678000195", 6, TOKEN)
		self.assertEqual(ctx.exception.code, 200)
		self.assertTrue(ctx.exception.is_document_error)

	def test_rate_limit_code(self):
		body = {"status": 0, "erroCodigo": 1007, "erro": "rate limit"}
		session = _FakeSession(_FakeResponse(429, _json_body(body)))
		with _patch_session(session):
			with self.assertRaises(client.RegistryLookupError) as ctx:
				client.fetch("12345678000195", 6, TOKEN)
		self.assertEqual(ctx.exception.code, 1007)
		self.assertFalse(ctx.exception.is_document_error)

	def test_timeout_is_transport_error(self):
		session = _FakeSession(exc=requests.exceptions.Timeout("timed out"))
		with _patch_session(session), mock.patch.object(client.frappe, "log_error"):
			with self.assertRaises(client.RegistryLookupError) as ctx:
				client.fetch("12345678000195", 6, TOKEN)
		self.assertEqual(ctx.exception.code, 0)

	def test_invalid_json_is_transport_error(self):
		session = _FakeSession(_FakeResponse(200, b"<html>not json</html>"))
		with _patch_session(session), mock.patch.object(client.frappe, "log_error"):
			with self.assertRaises(client.RegistryLookupError) as ctx:
				client.fetch("12345678000195", 6, TOKEN)
		self.assertEqual(ctx.exception.code, 0)

	def test_oversized_response_is_rejected(self):
		session = _FakeSession(_FakeResponse(200, b"x" * 100))
		with (
			_patch_session(session),
			mock.patch.object(client, "MAX_RESPONSE_BYTES", 10),
			mock.patch.object(client.frappe, "log_error"),
		):
			with self.assertRaises(client.RegistryLookupError) as ctx:
				client.fetch("12345678000195", 6, TOKEN)
		self.assertEqual(ctx.exception.code, 0)

	def test_redirect_is_not_followed(self):
		# A 302 with an empty body: allow_redirects=False keeps it as a 302, whose empty
		# body is not valid JSON, so it surfaces as a transport-class error.
		session = _FakeSession(_FakeResponse(302, b""))
		with _patch_session(session), mock.patch.object(client.frappe, "log_error"):
			with self.assertRaises(client.RegistryLookupError):
				client.fetch("12345678000195", 6, TOKEN)
		self.assertIs(session.get_kwargs["allow_redirects"], False)

	def test_token_is_masked_in_transport_log(self):
		url = f"https://api.cpfcnpj.com.br/{TOKEN}/6/12345678000195"
		session = _FakeSession(exc=requests.exceptions.ConnectionError(url))
		with _patch_session(session), mock.patch.object(client.frappe, "log_error") as log:
			with self.assertRaises(client.RegistryLookupError):
				client.fetch("12345678000195", 6, TOKEN)
		logged = log.call_args.kwargs["message"]
		self.assertNotIn(TOKEN, logged)
		self.assertIn("***", logged)
