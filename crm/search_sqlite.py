# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from typing import ClassVar

import frappe
from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from frappe.search.sqlite_search import SQLiteSearch

PARENT_DOCTYPES = ["CRM Lead", "CRM Deal"]
QUOTE_SELECTORS = "blockquote, .gmail_quote, .yahoo_quoted"

# Past this many readable records the IN (...) pre-filter gets too large, so hits are
# permission-checked after the search instead.
PREFILTER_LIMIT = 500


class CRMSearch(SQLiteSearch):
	INDEX_NAME = "crm_search.db"

	INDEX_SCHEMA: ClassVar = {
		"metadata_fields": ["parent", "author"],
	}

	INDEXABLE_DOCTYPES: ClassVar = {
		"Comment": {
			"fields": [
				"name",
				"content",
				"modified",
				"comment_type",
				"reference_doctype",
				"reference_name",
				{"author": "comment_email"},
			],
			"filters": {
				"comment_type": "Comment",
				"reference_doctype": ("in", PARENT_DOCTYPES),
			},
		},
		"FCRM Note": {
			"fields": [
				"name",
				"title",
				"content",
				"modified",
				"reference_doctype",
				"reference_docname",
				{"author": "owner"},
			],
			"filters": {"reference_doctype": ("in", PARENT_DOCTYPES)},
		},
		"Communication": {
			"fields": [
				"name",
				{"title": "subject"},
				"content",
				"modified",
				"communication_type",
				"communication_medium",
				"reference_doctype",
				"reference_name",
				{"author": "sender"},
			],
			"filters": {
				"communication_type": "Communication",
				"communication_medium": "Email",
				"reference_doctype": ("in", PARENT_DOCTYPES),
			},
		},
	}

	# search() can return before get_search_filters() runs, so it needs a resting value.
	is_post_filter_required = False

	def get_search_filters(self) -> dict:
		parents = self.get_readable_parents()
		self.is_post_filter_required = parents is None
		return {} if parents is None else {"parent": parents}

	def get_readable_parents(self) -> list[str] | None:
		"""Return `parent` keys the user can read, or None when there are too many to pre-filter.

		Includes the source Lead of each readable Deal, so a Deal reader also finds its Lead's activity.
		"""
		leads = frappe.get_list("CRM Lead", pluck="name", limit=PREFILTER_LIMIT + 1)
		deals = frappe.get_list("CRM Deal", fields=["name", "lead"], limit=PREFILTER_LIMIT + 1)
		if len(leads) > PREFILTER_LIMIT or len(deals) > PREFILTER_LIMIT:
			return None

		lead_names = set(leads) | {deal.lead for deal in deals if deal.lead}
		return [parent_key("CRM Lead", name) for name in lead_names] + [
			parent_key("CRM Deal", deal.name) for deal in deals
		]

	def prepare_document(self, doc):
		# The index queue loads documents by name, so the configured filters are not applied there.
		config = self.doc_configs.get(doc.doctype)
		if not config or not matches_filters(doc, config["filters"]):
			return None

		document = super().prepare_document(doc)
		if not document:
			return None

		reference_name = doc.reference_docname if doc.doctype == "FCRM Note" else doc.reference_name
		document["parent"] = parent_key(doc.reference_doctype, reference_name)

		# Index only the new text of an email, so a phrase matches the email that said it
		# and not every later reply that quotes it.
		if doc.doctype == "Communication":
			document["content"] = self._process_content(strip_quoted_reply(doc.content))
		return document

	def index_doc(self, doctype, docname):
		try:
			super().index_doc(doctype, docname)
		except Exception:
			frappe.log_error(title=f"CRM search: failed to index {doctype} {docname}")

	def remove_doc(self, doctype, docname):
		try:
			super().remove_doc(doctype, docname)
		except Exception:
			frappe.log_error(title=f"CRM search: failed to remove {doctype} {docname}")


def parent_key(doctype: str, name: str) -> str:
	return f"{doctype}:{name}"


def strip_quoted_reply(html: str) -> str:
	soup = BeautifulSoup(html, "html.parser")
	for quote in soup.select(QUOTE_SELECTORS):
		quote.decompose()
	return EmailReplyParser.parse_reply(soup.get_text("\n"))


def matches_filters(doc, filters: dict) -> bool:
	for field, value in filters.items():
		actual = doc.get(field)
		if isinstance(value, tuple):
			if actual not in value[1]:
				return False
		elif actual != value:
			return False
	return True
