# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""CPF / CNPJ validation and normalization (no framework coupling).

Pure, unit-testable helpers shared by the client (guarding the lookup) and the API
layer (rejecting an invalid document before enqueuing a paid call). CNPJ supports the
alphanumeric format (IN RFB 2.229/2024, in force from July 2026): 12 alphanumeric
positions plus 2 numeric check digits, with the modulo-11 sum computed over
``ord(c) - 48`` (so ``'0'`` weighs 0, ``'9'`` weighs 9, ``'A'`` weighs 17). Numeric
CNPJs stay valid. This module imports nothing from Frappe on purpose.
"""

from __future__ import annotations

import re

# CPF = 11 numeric digits; CNPJ = 12 alphanumeric positions + 2 numeric check digits.
CPF_LENGTH = 11
CNPJ_LENGTH = 14

_NON_ALNUM = re.compile(r"[^0-9A-Za-z]")


def normalize_document(value: str) -> str:
	"""Strip every non-alphanumeric character and upper-case the rest.

	Never use ``[^0-9]`` on a CNPJ: it would discard the letters of an alphanumeric
	CNPJ. The upper-case keeps the modulo-11 weighting deterministic (``'a'`` and
	``'A'`` must weigh the same).
	"""
	return _NON_ALNUM.sub("", value or "").upper()


def is_valid_cpf(value: str) -> bool:
	"""True if ``value`` is a well-formed CPF (11 numeric digits, valid check digits).

	Rejects the eleven repeated-digit sequences (``000...``/``111...``), which pass
	the arithmetic but are never issued.
	"""
	cpf = normalize_document(value)
	if len(cpf) != CPF_LENGTH or not cpf.isdigit() or cpf == cpf[0] * CPF_LENGTH:
		return False
	for i in (9, 10):
		total = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
		check = (total * 10) % 11 % 10
		if check != int(cpf[i]):
			return False
	return True


def is_valid_cnpj(value: str) -> bool:
	"""True if ``value`` is a well-formed CNPJ (numeric or alphanumeric).

	14 positions: 12 alphanumeric plus 2 numeric check digits. The check digits are
	always numeric; the first 12 positions may carry letters. Repeated-character
	sequences are rejected.
	"""
	cnpj = normalize_document(value)
	if len(cnpj) != CNPJ_LENGTH or not cnpj[12:].isdigit() or cnpj == cnpj[0] * CNPJ_LENGTH:
		return False
	values = [ord(c) - 48 for c in cnpj]
	for pos in (12, 13):
		weights = list(range(pos - 7, 1, -1)) + list(range(9, 1, -1))
		total = sum(v * w for v, w in zip(values[:pos], weights, strict=False))
		remainder = total % 11
		check = 0 if remainder < 2 else 11 - remainder
		if check != values[pos]:
			return False
	return True


def document_kind(value: str) -> str | None:
	"""Classify ``value`` as ``"cnpj"``, ``"cpf"`` or ``None`` (neither is valid).

	CNPJ is checked first: the two lengths never collide (14 vs 11), so ordering only
	decides the label for malformed input, which is ``None`` either way.
	"""
	if is_valid_cnpj(value):
		return "cnpj"
	if is_valid_cpf(value):
		return "cpf"
	return None
