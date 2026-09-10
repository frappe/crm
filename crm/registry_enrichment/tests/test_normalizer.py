# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for the package-6 payload normalizer (no framework, no network)."""

from __future__ import annotations

import copy

from frappe.tests import UnitTestCase

from crm.registry_enrichment.normalizer import (
	_iso_date,
	_parse_share_capital,
	title_case,
	to_result,
)
from crm.registry_enrichment.tests.fixtures import cnpj_package6
from crm.registry_enrichment.validators import is_valid_cnpj, normalize_document


def _cnpj_check_digits(base12: str) -> str:
	"""Compute the two numeric CNPJ check digits for a 12-position alphanumeric base.

	Mirrors ``validators.is_valid_cnpj``: modulo-11 over ``ord(c) - 48`` with the same
	weight vector, so a base such as ``"12ABC34501DE"`` yields a document that passes
	``is_valid_cnpj``."""
	chars = list(base12)
	for pos in (12, 13):
		weights = list(range(pos - 7, 1, -1)) + list(range(9, 1, -1))
		values = [ord(c) - 48 for c in chars]
		total = sum(v * w for v, w in zip(values, weights, strict=True))
		remainder = total % 11
		chars.append(str(0 if remainder < 2 else 11 - remainder))
	return "".join(chars[12:])


class TitleCaseTest(UnitTestCase):
	def test_keeps_legal_acronyms_upper(self):
		self.assertEqual(title_case("TOKEN TEST LTDA"), "Token Test LTDA")

	def test_lowercases_prepositions(self):
		self.assertEqual(title_case("EMPRESA DE PEQUENO PORTE"), "Empresa de Pequeno Porte")

	def test_empty(self):
		self.assertEqual(title_case(""), "")
		self.assertEqual(title_case(None), "")


class ToResultTest(UnitTestCase):
	def setUp(self):
		self.payload = cnpj_package6()
		self.result = to_result(self.payload)

	def test_legal_and_trade_name(self):
		self.assertEqual(self.result.get("legal_name"), "Token Test LTDA")
		self.assertEqual(self.result.get("trade_name"), "Token Test")

	def test_tax_id_is_digits_only(self):
		self.assertEqual(self.result.get("tax_id"), "12345678000195")

	def test_tax_id_preserves_alphanumeric_cnpj(self):
		# IN RFB 2.229/2024: the first 12 positions may carry letters. tax_id must be
		# normalized with normalize_document (letters kept, upper-cased, punctuation
		# stripped), never digits-only, and must equal the value the client/URL keys on.
		base = "12ABC34501DE"
		cnpj = base + _cnpj_check_digits(base)
		self.assertTrue(is_valid_cnpj(cnpj))
		payload = copy.deepcopy(self.payload)
		# Feed it punctuated and lower-cased to prove normalization, not passthrough.
		payload["cnpj"] = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}".lower()
		result = to_result(payload)
		self.assertEqual(result.get("tax_id"), cnpj)
		self.assertEqual(result.get("tax_id"), normalize_document(payload["cnpj"]))

	def test_tolerates_non_string_legal_nature_code(self):
		payload = copy.deepcopy(self.payload)
		payload["naturezaJuridica"] = {"codigo": 2062, "descricao": "SOCIEDADE EMPRESARIA LIMITADA"}
		self.assertEqual(to_result(payload).get("legal_nature"), "2062 - Sociedade Empresaria Limitada")

	def test_tolerates_non_string_address_number(self):
		payload = copy.deepcopy(self.payload)
		payload["matrizEndereco"]["numero"] = 1
		self.assertEqual(to_result(payload).address["address_line1"], "Rua Das Flores, 1")

	def test_tolerates_bool_optante(self):
		payload = copy.deepcopy(self.payload)
		payload["simplesNacional"] = {"optante": True}
		self.assertEqual(to_result(payload).get("simples_nacional"), 1)
		payload["simplesNacional"] = {"optante": False}
		self.assertEqual(to_result(payload).get("simples_nacional"), 0)

	def test_tolerates_int_optante(self):
		payload = copy.deepcopy(self.payload)
		payload["simplesNacional"] = {"optante": 1}
		self.assertEqual(to_result(payload).get("simples_nacional"), 1)
		payload["simplesNacional"] = {"optante": 0}
		self.assertEqual(to_result(payload).get("simples_nacional"), 0)

	def test_tolerates_string_variants_optante(self):
		for raw, expected in (("Sim", 1), ("S", 1), ("Não", 0), ("N", 0)):
			payload = copy.deepcopy(self.payload)
			payload["simplesNacional"] = {"optante": raw}
			self.assertEqual(to_result(payload).get("simples_nacional"), expected, raw)

	def test_tolerates_non_dict_regime_element(self):
		payload = copy.deepcopy(self.payload)
		payload["regimesTributarios"] = ["garbage", {"ano": 2021, "regime_tributario": "LUCRO PRESUMIDO"}]
		self.assertEqual(to_result(payload).get("tax_regime"), "Lucro Presumido")

	def test_invalid_opening_date_is_dropped_not_raised(self):
		payload = copy.deepcopy(self.payload)
		payload["inicioAtividade"] = "31/13/2020"
		result = to_result(payload)
		# The impossible date is omitted and the rest of the enrichment still resolves.
		self.assertNotIn("opening_date", result.fields)
		self.assertEqual(result.get("legal_name"), "Token Test LTDA")

	def test_registration_status_maps_to_english(self):
		self.assertEqual(self.result.get("registration_status"), "Unfit")

	def test_dates_are_iso(self):
		self.assertEqual(self.result.get("opening_date"), "1999-12-31")
		self.assertEqual(self.result.get("registration_status_date"), "2020-04-03")

	def test_legal_nature_carries_code_and_description(self):
		self.assertEqual(self.result.get("legal_nature"), "2062 - Sociedade Empresaria Limitada")

	def test_company_size_and_share_capital(self):
		self.assertEqual(self.result.get("company_size"), "Empresa de Pequeno Porte")
		self.assertEqual(self.result.get("share_capital"), 95000.0)

	def test_tax_regime_is_most_recent_year(self):
		# 2019 = Simples Nacional, 2021 = Lucro Presumido; the latest year wins.
		self.assertEqual(self.result.get("tax_regime"), "Lucro Presumido")

	def test_simples_nacional_bool(self):
		self.assertEqual(self.result.get("simples_nacional"), 0)

	def test_industry_and_section(self):
		self.assertEqual(
			self.result.get("industry"),
			"Desenvolvimento e Licenciamento de Programas de Computador Customizaveis",
		)
		self.assertEqual(self.result.get("industry_section"), "Technology")

	def test_email_is_lowercased(self):
		self.assertEqual(self.result.get("email"), "contato@empresa.com")

	def test_phone_is_e164(self):
		self.assertEqual(self.result.get("phone"), "+551122334454")

	def test_no_mobile_when_single_phone(self):
		self.assertIsNone(self.result.get("mobile_no"))

	def test_mobile_no_from_second_phone(self):
		payload = copy.deepcopy(self.payload)
		payload["telefones"].append({"ddd": "31", "numero": "40421005"})
		result = to_result(payload)
		self.assertEqual(result.get("mobile_no"), "+553140421005")

	def test_address_shape(self):
		address = self.result.address
		self.assertIsNotNone(address)
		self.assertEqual(address["address_line1"], "Rua Das Flores, 1")
		self.assertEqual(address["address_line2"], "Sala 1 - Centro")
		self.assertEqual(address["city"], "Montes Claros")
		self.assertEqual(address["state"], "MG")
		self.assertEqual(address["pincode"], "39400000")
		self.assertEqual(address["country"], "Brazil")

	def test_absent_keys_are_not_emitted(self):
		# A payload with no situacao must not carry a registration_status key at all,
		# so a Fill-if-empty mapping never writes a blank.
		payload = copy.deepcopy(self.payload)
		payload.pop("situacao")
		result = to_result(payload)
		self.assertNotIn("registration_status", result.fields)


class ShareCapitalTest(UnitTestCase):
	def test_accepts_int(self):
		self.assertEqual(_parse_share_capital(1000), 1000.0)

	def test_accepts_float(self):
		self.assertEqual(_parse_share_capital(1000.5), 1000.5)

	def test_accepts_us_decimal_string(self):
		self.assertEqual(_parse_share_capital("1000.00"), 1000.0)

	def test_accepts_brazilian_string(self):
		self.assertEqual(_parse_share_capital("1.000,00"), 1000.0)

	def test_accepts_currency_prefixed_string(self):
		self.assertEqual(_parse_share_capital("R$ 1.000,00"), 1000.0)

	def test_unparseable_is_none(self):
		self.assertIsNone(_parse_share_capital("n/a"))
		self.assertIsNone(_parse_share_capital(None))

	def test_result_reads_string_capital(self):
		payload = cnpj_package6()
		payload["capitalSocial"] = "R$ 1.000,00"
		self.assertEqual(to_result(payload).get("share_capital"), 1000.0)


class IsoDateTest(UnitTestCase):
	def test_valid_date(self):
		self.assertEqual(_iso_date("31/12/1999"), "1999-12-31")

	def test_invalid_calendar_date_is_empty(self):
		self.assertEqual(_iso_date("31/13/2020"), "")
		self.assertEqual(_iso_date("31/02/1999"), "")

	def test_empty_and_none_are_empty(self):
		self.assertEqual(_iso_date(""), "")
		self.assertEqual(_iso_date(None), "")
