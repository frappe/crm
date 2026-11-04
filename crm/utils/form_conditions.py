# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A web form field's conditions (depends_on, mandatory_depends_on,
read_only_depends_on), evaluated on the server the way the public form page
evaluates them in the browser (crm/templates/includes/crm_form_logic.js).

The browser only decides what to show. These decide what a submission must
contain, so a script or an agent posting straight to the API gets the same rules
as someone filling in the page.

Expressions are parsed, never executed: doc/parent access, literals, comparisons,
&& || ! and parentheses. Anything else falls back, as on the page.
"""

import re

import frappe
from frappe import _

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_NAME = re.compile(r"[A-Za-z_$][\w$]*")
_OPERATORS = ("===", "!==", "==", "!=", "<=", ">=", "<", ">")
_UNDEFINED = object()


class _Unsupported(Exception):
	pass


def form_value_errors(fields, values: dict) -> str | None:
	"""The first answer a submission is missing, as a message, else None. A field
	counts only while the form shows it and it isn't read-only."""
	for f in fields:
		if f.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue
		if not field_required(f, values):
			continue
		value = values.get(f.fieldname)
		if value in (None, "", 0) or (isinstance(value, str) and not value.strip()):
			return _("Please fill in: {0}").format(f.label or f.fieldname)
	return None


def check_form_values(fields, values: dict):
	if error := form_value_errors(fields, values):
		frappe.throw(error)


def field_visible(f, doc: dict) -> bool:
	return truthy(f.get("depends_on"), doc, True)


def field_required(f, doc: dict) -> bool:
	required = bool(f.get("reqd")) or truthy(f.get("mandatory_depends_on"), doc, False)
	return required and field_visible(f, doc) and not truthy(f.get("read_only_depends_on"), doc, False)


def truthy(expr, doc: dict, fallback: bool) -> bool:
	"""A field condition: "eval:<expression>", or a fieldname that must be set."""
	s = str(expr or "").strip()
	if not s:
		return fallback
	try:
		if s.startswith("eval:"):
			return _coerce(_Parser(s[5:], doc).parse())
		if s.startswith("fn:"):
			return fallback
		return _coerce(doc.get(s))
	except _Unsupported:
		return fallback


def _coerce(value) -> bool:
	"""JavaScript truthiness: "0" is true, "" and 0 are false."""
	if value is _UNDEFINED or value is None:
		return False
	if isinstance(value, list | tuple | dict):
		return len(value) > 0
	return bool(value)


def _number(value):
	if isinstance(value, bool):
		return int(value)
	if isinstance(value, int | float):
		return value
	if isinstance(value, str):
		value = value.strip()
		if value == "":
			return 0
		try:
			return float(value)
		except ValueError:
			return None
	return None


def _loose_equal(a, b) -> bool:
	"""JavaScript ==, for the values a form holds (strings, numbers, booleans, null)."""
	a = None if a is _UNDEFINED else a
	b = None if b is _UNDEFINED else b
	if a is None or b is None:
		return a is None and b is None
	if isinstance(a, str) and isinstance(b, str):
		return a == b
	left, right = _number(a), _number(b)
	if left is None or right is None:
		return False
	return left == right


def _compare(op, a, b) -> bool:
	if op in ("==", "==="):
		return _loose_equal(a, b)
	if op in ("!=", "!=="):
		return not _loose_equal(a, b)
	if isinstance(a, str) and isinstance(b, str):
		left, right = a, b
	else:
		left, right = _number(a), _number(b)
		if left is None or right is None:
			return False
	return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[op]


class _Parser:
	def __init__(self, src: str, doc: dict):
		self.src, self.i, self.doc = src, 0, doc

	def parse(self):
		value = self.or_expr()
		self.ws()
		if self.i < len(self.src):
			raise _Unsupported("trailing input")
		return value

	def ws(self):
		while self.i < len(self.src) and self.src[self.i].isspace():
			self.i += 1

	def starts(self, token: str) -> bool:
		self.ws()
		return self.src.startswith(token, self.i)

	def or_expr(self):
		left = self.and_expr()
		while self.starts("||"):
			self.i += 2
			right = self.and_expr()
			left = _coerce(left) or _coerce(right)
		return left

	def and_expr(self):
		left = self.comparison()
		while self.starts("&&"):
			self.i += 2
			right = self.comparison()
			left = _coerce(left) and _coerce(right)
		return left

	def comparison(self):
		left = self.primary()
		self.ws()
		for op in _OPERATORS:
			if self.src.startswith(op, self.i):
				self.i += len(op)
				return _compare(op, left, self.primary())
		return left

	def primary(self):
		self.ws()
		if self.starts("("):
			self.i += 1
			value = self.or_expr()
			if not self.starts(")"):
				raise _Unsupported("expected )")
			self.i += 1
			return value
		if self.starts("!") and not self.src.startswith("!=", self.i):
			self.i += 1
			return not _coerce(self.primary())
		if self.i >= len(self.src):
			raise _Unsupported("unexpected end")
		quote = self.src[self.i]
		if quote in ("'", '"'):
			return self.string(quote)
		if number := _NUMBER.match(self.src, self.i):
			self.i = number.end()
			return float(number.group())
		name = _NAME.match(self.src, self.i)
		if not name:
			raise _Unsupported("unexpected token")
		self.i = name.end()
		word = name.group()
		if word in ("true", "false", "null"):
			return {"true": True, "false": False, "null": None}[word]
		if word not in ("doc", "parent"):
			raise _Unsupported(f"unknown identifier: {word}")
		return self.members(self.doc)

	def string(self, quote: str) -> str:
		self.i += 1
		out = []
		while self.i < len(self.src) and self.src[self.i] != quote:
			if self.src[self.i] == "\\":
				self.i += 1
			if self.i < len(self.src):
				out.append(self.src[self.i])
			self.i += 1
		self.i += 1
		return "".join(out)

	def members(self, base):
		while True:
			self.ws()
			if self.src.startswith(".", self.i):
				self.i += 1
				name = _NAME.match(self.src, self.i)
				if not name:
					raise _Unsupported("bad member")
				self.i = name.end()
				base = self.member(base, name.group())
			elif self.src.startswith("[", self.i):
				self.i += 1
				key = self.or_expr()
				if not self.starts("]"):
					raise _Unsupported("expected ]")
				self.i += 1
				base = self.member(base, key)
			else:
				return base

	@staticmethod
	def member(base, key):
		if isinstance(base, dict):
			return base.get(str(key), _UNDEFINED)
		return _UNDEFINED
