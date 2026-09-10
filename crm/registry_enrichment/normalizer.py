# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Translate a CPF.CNPJ package-6 payload into a mappable ``RegistryResult``.

``EnrichmentResult`` (from ``domain_enrichment.result``) has a fixed, web-crawl-shaped
schema (company_name / description / logo / social profiles) with no home for fiscal
fields such as ``tax_id``, ``registration_status`` or a structured address, and its
mapper resolves a closed set of source keys. Rather than bend registry data into that
shape, this module produces a minimal ``RegistryResult``: a flat
``{source_key: value}`` bag plus an optional structured ``address`` dict, consumed by
this module's own ``mapper.apply_to_document``. It reuses the domain module's
write-policy mechanics (see ``registry_enrichment.mapper``), not its result container.

The Receita returns everything in upper case; ``title_case`` restores readable casing
while keeping legal acronyms (LTDA, S/A, ME, EPP, EIRELI) upper and Portuguese
prepositions (de/da/do/das/dos/e) lower. Only keys with a real value are emitted, so a
``Fill if empty`` mapping never overwrites a field with an empty string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from .validators import normalize_document

# Provenance label recorded on the Run for every registry-sourced value.
METHOD = "Registry API"

# Legal acronyms kept upper-case; prepositions kept lower-case (not at position 0).
_ACRONYMS = {"LTDA", "S.A.", "S/A", "SA", "ME", "EPP", "EIRELI", "MEI", "EI", "S.A", "CIA"}
_PREPOSITIONS = {"de", "da", "do", "das", "dos", "e"}

# Portuguese registration status (situacao.nome) -> English Select option.
_STATUS_MAP = {
	"ativa": "Active",
	"suspensa": "Suspended",
	"inapta": "Unfit",
	"baixada": "Closed",
	"nula": "Null",
}

# CNAE section letter -> stable industry label (the 10 sections a CRM cares about).
_CNAE_SECTIONS = {
	"A": "Agriculture",
	"C": "Manufacturing",
	"F": "Construction",
	"G": "Retail",
	"H": "Logistics",
	"I": "Hospitality",
	"J": "Technology",
	"K": "Finance",
	"P": "Education",
	"Q": "Healthcare",
}


@dataclass
class RegistryResult:
	"""A flat bag of mappable values plus an optional structured address.

	``fields`` holds ``source_key -> scalar``; ``address`` holds the Frappe Address
	shape (address_line1/address_line2/city/state/pincode/country) or ``None``. Only
	keys with a real value are ever added, so the mapper can treat any absent key as
	"nothing to fill".
	"""

	fields: dict = field(default_factory=dict)
	address: dict | None = None

	def get(self, source_key: str):
		"""Resolve one source key to its scalar value (``None`` when absent)."""
		return self.fields.get(source_key)


def title_case(text: str) -> str:
	"""Readable casing for an upper-case Receita string, preserving legal acronyms
	and lower-casing prepositions that are not the first word."""
	if not text:
		return ""
	words = str(text).split()
	out = []
	for index, word in enumerate(words):
		upper = word.upper()
		if upper in _ACRONYMS:
			out.append(upper)
			continue
		lower = word.lower()
		if index > 0 and lower in _PREPOSITIONS:
			out.append(lower)
			continue
		out.append(word.capitalize())
	return " ".join(out)


def _text(value) -> str:
	"""Coerce any scalar payload value to a stripped string (``""`` for ``None``).

	The registry API types some fields inconsistently: a code or a house number can
	arrive as an ``int``, an ``optante`` flag as a JSON ``bool``. Centralizing the
	coercion keeps the ``.strip()`` / ``.lower()`` call sites from raising
	``AttributeError`` on a non-string and turning the whole enrichment into a Failed
	run. A ``bool`` becomes ``"True"`` / ``"False"`` (so ``.lower()`` yields the
	``"true"`` / ``"false"`` the optante parser already recognizes)."""
	if value is None:
		return ""
	return str(value).strip()


def _iso_date(value) -> str:
	"""Convert a ``dd/mm/aaaa`` string to ISO ``aaaa-mm-dd``; ``""`` when unparseable.

	The calendar is validated with ``datetime.strptime`` so an impossible date such as
	``"31/13/2020"`` or ``"31/02/1999"`` yields ``""`` (the field is omitted) instead of
	being written to a Frappe ``Date`` field and aborting the whole ``doc.save()``.
	"""
	parts = _text(value).split("/")
	if len(parts) != 3:
		return ""
	day, month, year = (p.strip() for p in parts)
	if not (day.isdigit() and month.isdigit() and year.isdigit()):
		return ""
	iso = f"{year:0>4}-{month:0>2}-{day:0>2}"
	try:
		datetime.strptime(iso, "%Y-%m-%d")
	except ValueError:
		return ""
	return iso


def _digits(value: str) -> str:
	return "".join(ch for ch in str(value or "") if ch.isdigit())


def _parse_share_capital(value) -> float | None:
	"""Parse ``capitalSocial`` from an int, a float or a formatted string.

	The API has been seen to send the share capital as a number (``95000``) or as a
	formatted string in either US (``"1000.00"``) or Brazilian (``"1.000,00"``,
	``"R$ 1.000,00"``) notation. Returns a ``float`` (``None`` when unparseable).

	Brazilian notation uses ``.`` for thousands and ``,`` for the decimal, so when a
	comma is present the dots are dropped and the comma becomes the decimal point.
	Without a comma the string is read as-is (US decimal or a plain integer).
	"""
	if isinstance(value, bool):
		return None
	if isinstance(value, int | float):
		return float(value)
	if not isinstance(value, str):
		return None
	# Keep only digits, separators and a leading sign; strips "R$", spaces, NBSPs.
	text = re.sub(r"[^\d,.-]", "", value)
	if not text:
		return None
	if "," in text:
		text = text.replace(".", "").replace(",", ".")
	try:
		return float(text)
	except ValueError:
		return None


def _phone_e164(entry: dict) -> str:
	"""Build an E.164 ``+55`` number from a ``telefones[]`` entry; ``""`` when empty."""
	if not isinstance(entry, dict):
		return ""
	ddd = _digits(entry.get("ddd"))
	number = _digits(entry.get("numero"))
	if not ddd or not number:
		return ""
	return f"+55{ddd}{number}"


def _most_recent_regime(regimes) -> str:
	"""The ``regime_tributario`` of the most recent year in ``regimesTributarios``."""
	if not isinstance(regimes, list):
		return ""
	regimes = [r for r in regimes if isinstance(r, dict)]
	if not regimes:
		return ""
	latest = max(regimes, key=lambda r: r.get("ano") or 0)
	return title_case(latest.get("regime_tributario") or "")


def _build_address(payload: dict) -> dict | None:
	"""Assemble the Frappe Address shape from ``matrizEndereco``; ``None`` when there
	is no usable street or city."""
	end = payload.get("matrizEndereco") or {}
	if not isinstance(end, dict):
		return None

	street = " ".join(p for p in (title_case(end.get("tipo")), title_case(end.get("logradouro"))) if p)
	number = _text(end.get("numero"))
	line1 = f"{street}, {number}".strip(", ") if number else street

	line2 = " - ".join(p for p in (title_case(end.get("complemento")), title_case(end.get("bairro"))) if p)
	city = title_case(end.get("cidade"))
	state = (end.get("uf") or "").strip().upper()
	pincode = _digits(end.get("cep"))
	if len(pincode) > 8:
		pincode = pincode[:8]

	if not line1 and not city:
		return None

	address = {"country": "Brazil"}
	if line1:
		address["address_line1"] = line1
	if line2:
		address["address_line2"] = line2
	if city:
		address["city"] = city
	if state:
		address["state"] = state
	if pincode:
		address["pincode"] = pincode
	return address


def to_result(payload: dict) -> RegistryResult:
	"""Map a package-6 (CNPJ D) payload to a ``RegistryResult``.

	Every field is added only when it resolves to a truthy value, so downstream
	``Fill if empty`` mappings never write blanks over user data.
	"""
	fields: dict = {}

	def put(key, value):
		if value not in (None, "", []):
			fields[key] = value

	put("legal_name", title_case(payload.get("razao")))
	put("trade_name", title_case(payload.get("fantasia")))
	put("tax_id", normalize_document(payload.get("cnpj") or "") or None)

	situacao = payload.get("situacao") or {}
	if isinstance(situacao, dict):
		put("registration_status", _STATUS_MAP.get((situacao.get("nome") or "").strip().lower()))
		put("registration_status_date", _iso_date(situacao.get("data")))

	put("opening_date", _iso_date(payload.get("inicioAtividade")))

	natureza = payload.get("naturezaJuridica") or {}
	if isinstance(natureza, dict) and natureza.get("descricao"):
		codigo = _text(natureza.get("codigo"))
		descricao = title_case(natureza.get("descricao"))
		put("legal_nature", f"{codigo} - {descricao}".strip(" -"))

	porte = payload.get("porte") or {}
	if isinstance(porte, dict):
		put("company_size", title_case(porte.get("descricao")))

	capital = _parse_share_capital(payload.get("capitalSocial"))
	if capital is not None:
		put("share_capital", capital)

	put("tax_regime", _most_recent_regime(payload.get("regimesTributarios")))

	simples = payload.get("simplesNacional") or {}
	if isinstance(simples, dict) and simples.get("optante") is not None:
		optante = _text(simples.get("optante")).lower()
		put("simples_nacional", 1 if optante in ("sim", "s", "true", "1") else 0)

	cnae = payload.get("cnae") or {}
	if isinstance(cnae, dict):
		put("industry", title_case(cnae.get("descricao")))
		put("industry_section", _CNAE_SECTIONS.get((cnae.get("secao") or "").strip().upper()))

	put("email", (payload.get("email") or "").strip().lower())

	telefones = payload.get("telefones") or []
	if isinstance(telefones, list):
		if telefones:
			put("phone", _phone_e164(telefones[0]))
		if len(telefones) > 1:
			put("mobile_no", _phone_e164(telefones[1]))

	return RegistryResult(fields=fields, address=_build_address(payload))
