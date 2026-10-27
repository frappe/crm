# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
from dataclasses import dataclass
from functools import cached_property

import frappe
from frappe import _

# Allowlist: fieldtypes that read well in a table cell. Passwords, attachments, HTML and tables never show.
COLUMN_FIELDTYPES = frozenset(
	(
		"Autocomplete",
		"Check",
		"Currency",
		"Data",
		"Date",
		"Datetime",
		"Duration",
		"Float",
		"Int",
		"Link",
		"Percent",
		"Phone",
		"Rating",
		"Select",
		"Small Text",
		"Time",
	)
)
STANDARD_FIELDS = {"creation": "Created On", "modified": "Last Modified"}
WIDTH_PATTERN = re.compile(r"^(\d{1,4}(\.\d{1,2})?(px|rem|fr)?|minmax\(0,\d{1,2}(\.\d)?fr\))$")
MAX_LABEL_LENGTH = 140


@dataclass(frozen=True)
class Alias:
	label: str
	fieldtype: str
	options: str
	fields: dict


# Leads and deals name some fields differently; an alias shows them as one column.
ALIASES = {
	"owner": Alias("Owner", "Link", "User", {"CRM Lead": "lead_owner", "CRM Deal": "deal_owner"}),
}


class ColumnFields:
	"""Fields `user` may add as columns to a widget showing `doctypes`.

	A widget showing several doctypes offers the fields they share, with the same fieldtype, plus aliases.
	"""

	def __init__(self, doctypes: tuple, user: str | None = None):
		self.doctypes = doctypes
		self.user = user or frappe.session.user

	@cached_property
	def available(self) -> dict:
		per_doctype = [self.by_doctype[doctype] for doctype in self.doctypes]
		if len(per_doctype) == 1:
			return per_doctype[0]

		first, *others = per_doctype
		shared = {
			key: field
			for key, field in first.items()
			if all(other.get(key, {}).get("fieldtype") == field["fieldtype"] for other in others)
		}
		return {**shared, **self._aliases()}

	@cached_property
	def by_doctype(self) -> dict:
		return {doctype: self._fields(doctype) for doctype in self.doctypes}

	def term(self, doctype: str, table, key: str):
		if key in ALIASES:
			return table[ALIASES[key].fields[doctype]].as_(key)
		return table[key]

	def currency_field(self, doctype: str, key: str) -> str | None:
		"""The field holding the row's currency, so cells format in it."""
		if self.available[key]["fieldtype"] != "Currency" or key in ALIASES:
			return None
		options = frappe.get_meta(doctype).get_field(key).options
		return options if options in self.by_doctype[doctype] else None

	def _fields(self, doctype: str) -> dict:
		meta = frappe.get_meta(doctype)
		permitted = set(meta.get_permitted_fieldnames(user=self.user, with_virtual_fields=False))
		fields = {
			df.fieldname: field(df.fieldname, _(df.label), df.fieldtype, df.options)
			for df in meta.fields
			if df.fieldname in permitted and not df.hidden and df.fieldtype in COLUMN_FIELDTYPES
		}
		standard = {key: field(key, _(label), "Datetime") for key, label in STANDARD_FIELDS.items()}
		return {**fields, **standard}

	def _aliases(self) -> dict:
		aliases = {}
		for key, alias in ALIASES.items():
			if all(alias.fields.get(doctype) in self.by_doctype[doctype] for doctype in self.doctypes):
				aliases[key] = field(key, _(alias.label), alias.fieldtype, alias.options)
		return aliases


class WidgetColumns:
	"""Columns stored in a widget's config: built-in ones from `spec`, the rest from `ColumnFields`."""

	def __init__(self, name: str, spec, doctypes: tuple, user: str | None = None):
		self.name = name
		self.spec = spec
		self.fields = ColumnFields(doctypes, user)

	def available(self) -> list:
		if not self.spec.columns:
			return []
		return [field for key, field in self.fields.available.items() if key not in self.spec.columns]

	def validate(self, columns) -> list:
		if not self.spec.columns:
			frappe.throw(_("Home widget {0} has no columns to edit").format(self.name))
		if not isinstance(columns, list):
			frappe.throw(_("Home widget {0} columns must be a list").format(self.name))

		keys = []
		for column in columns:
			key = column.get("key") if isinstance(column, dict) else None
			if not self._valid(column) or key in keys:
				frappe.throw(_("Home widget {0} cannot show column {1}").format(self.name, key))
			keys.append(key)

		if missing := [key for key in self.spec.locked if key not in keys]:
			frappe.throw(_("Home widget {0} must show {1}").format(self.name, ", ".join(missing)))
		return [clean(column) for column in columns]

	def allowed(self, columns: list | None) -> list | None:
		"""Saved columns the user may still see; None falls back to the defaults."""
		if not isinstance(columns, list) or not self.spec.columns:
			return None
		kept = [clean(column) for column in columns if self._valid(column)]
		keys = [column["key"] for column in kept]
		if len(set(keys)) != len(keys) or any(key not in keys for key in self.spec.locked):
			return None
		return kept

	def extra(self, columns: list | None) -> tuple:
		"""Keys the widget fetches on top of its built-in columns."""
		return tuple(
			column["key"] for column in self.allowed(columns) or () if column["key"] not in self.spec.columns
		)

	def _valid(self, column) -> bool:
		if not isinstance(column, dict) or set(column) - {"key", "label", "width"}:
			return False
		key, label, width = column.get("key"), column.get("label"), column.get("width")
		return (
			isinstance(key, str)
			and (key in self.spec.columns or key in self.fields.available)
			and (label is None or (isinstance(label, str) and len(label) <= MAX_LABEL_LENGTH))
			and (width is None or (isinstance(width, str) and bool(WIDTH_PATTERN.match(width))))
		)


def field(fieldname: str, label: str, fieldtype: str, options: str | None = None) -> dict:
	return {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "options": options}


def clean(column: dict) -> dict:
	return {k: column[k] for k in ("key", "label", "width") if column.get(k) is not None}
