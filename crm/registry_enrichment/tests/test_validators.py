# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for CPF / CNPJ validation and normalization (no framework, no network)."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from crm.registry_enrichment.validators import (
	document_kind,
	is_valid_cnpj,
	is_valid_cpf,
	normalize_document,
)


class NormalizeDocumentTest(UnitTestCase):
	def test_strips_punctuation_and_uppercases(self):
		self.assertEqual(normalize_document("12.345.678/0001-95"), "12345678000195")
		self.assertEqual(normalize_document("12abc34501de35"), "12ABC34501DE35")

	def test_handles_none_and_empty(self):
		self.assertEqual(normalize_document(None), "")
		self.assertEqual(normalize_document(""), "")


class CpfValidationTest(UnitTestCase):
	def test_valid_cpf(self):
		self.assertTrue(is_valid_cpf("111.444.777-35"))

	def test_bad_check_digit_cpf(self):
		self.assertFalse(is_valid_cpf("123.456.789-00"))

	def test_repeated_sequence_cpf(self):
		self.assertFalse(is_valid_cpf("000.000.000-00"))

	def test_wrong_length_cpf(self):
		self.assertFalse(is_valid_cpf("111.444.777-3"))


class CnpjValidationTest(UnitTestCase):
	def test_valid_numeric_cnpj(self):
		self.assertTrue(is_valid_cnpj("12.345.678/0001-95"))

	def test_valid_alphanumeric_cnpj(self):
		# IN RFB 2.229/2024: 12 alphanumeric positions + 2 numeric check digits.
		self.assertTrue(is_valid_cnpj("12ABC34501DE35"))

	def test_repeated_sequence_cnpj(self):
		self.assertFalse(is_valid_cnpj("11.111.111/1111-11"))

	def test_bad_check_digit_cnpj(self):
		self.assertFalse(is_valid_cnpj("12.345.678/0001-96"))

	def test_non_numeric_check_digits_rejected(self):
		# The last two positions must be numeric even for an alphanumeric CNPJ.
		self.assertFalse(is_valid_cnpj("12ABC34501DEAB"))


class DocumentKindTest(UnitTestCase):
	def test_classifies_cnpj(self):
		self.assertEqual(document_kind("12.345.678/0001-95"), "cnpj")

	def test_classifies_cpf(self):
		self.assertEqual(document_kind("111.444.777-35"), "cpf")

	def test_returns_none_for_garbage(self):
		self.assertIsNone(document_kind("not a document"))
		self.assertIsNone(document_kind(""))
