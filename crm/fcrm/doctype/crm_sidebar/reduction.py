"""Reduce the whole ordered list the dialog shows to the smallest layer that produces it.

The client sends what it shows, never anchors: a client that sent anchors would diff
against a copy of the layer below that may be stale.
"""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_sidebar.crm_sidebar import OWN_KEY, OWN_ROWS_PER_LAYER
from crm.fcrm.doctype.crm_sidebar.layers import OVERRIDABLE, as_item, is_own_key

TEXT_FIELDS = ("key", "type", "label", "icon", "link_type", "link_to", "parent_key")
OWN_FIELDS = ("key", "type", "label", "link_type", "link_to", "parent_key", "collapsible", "keep_closed")
CHECKS = ("collapsible", "keep_closed", "hidden")
BELOW = {"user": "site:", "site": None}


def reduce_layer(below: list[dict], desired: list[dict], scope: str) -> list[dict]:
	"""The rows a layer stores so that `below` resolves to `desired`."""
	below_by_key = {item["key"]: item for item in below}
	desired = known_items(desired, below_by_key, scope)
	check_nesting(desired)
	anchors = anchors_for(below, desired)

	rows = []
	for item in desired:
		key = item["key"]
		if key in below_by_key:
			row = delta(item, below_by_key[key], anchors.get(key))
		else:
			row = own_row(item, anchors.get(key))
		if row:
			rows.append(row)
	return rows


def known_items(desired: list[dict], below: dict[str, dict], scope: str) -> list[dict]:
	"""The items the layer below holds and the ones this layer adds, each key once."""
	seen, kept = set(), []

	for raw in desired:
		if not isinstance(raw, dict) or any(not isinstance(raw.get(f), str | None) for f in TEXT_FIELDS):
			frappe.throw(_("Each sidebar row must be an object with text fields."))
		item = as_item(raw)
		key = item["key"]
		if not isinstance(key, str) or key in seen:
			continue
		if key not in below and not (OWN_KEY.fullmatch(key) and key.startswith(f"{scope}:")):
			# Dropped quietly: an item a release removed, or a row the layer below deleted
			# while the dialog was open.
			dropped_below = BELOW[scope] and key.startswith(BELOW[scope])
			if is_own_key(key) and not dropped_below:
				frappe.throw(_("{0} is not a key this layer can add.").format(key))
			continue
		seen.add(key)
		kept.append(item)

	if sum(item["key"] not in below for item in kept) > OWN_ROWS_PER_LAYER:
		frappe.throw(_("You can add up to {0} rows to the sidebar.").format(OWN_ROWS_PER_LAYER))
	return kept


def check_nesting(desired: list[dict]):
	"""Sections stay at the top level, and items go only into a section a layer added."""
	custom_sections = {
		item["key"] for item in desired if item["type"] == "Section" and is_own_key(item["key"])
	}
	for item in desired:
		parent = item.get("parent_key")
		if not parent:
			continue
		if item["type"] == "Section" or parent not in custom_sections:
			frappe.throw(
				_("{0} cannot go under {1}. Items go only into a section you added.").format(
					item.get("label") or item["key"], parent
				)
			)


def delta(item: dict, below: dict, anchors: list[dict] | None) -> dict | None:
	"""A row naming what this layer changes on an item, or None when it changes nothing."""
	overrides = [field for field in OVERRIDABLE if differs(field, item, below)]
	if not overrides and not anchors:
		return None

	row = {"key": item["key"], "type": below["type"]}
	row.update({field: item[field] for field in overrides})
	if overrides:
		row["overrides"] = json.dumps(overrides)
	if anchors:
		row["anchors"] = json.dumps(anchors)
	return row


def differs(field: str, item: dict, below: dict) -> bool:
	if field in CHECKS:
		return int(bool(item.get(field))) != int(bool(below.get(field)))
	# A blank label or icon is no change: the item keeps the one below.
	return bool(item.get(field)) and item.get(field) != below.get(field)


def own_row(item: dict, anchors: list[dict] | None) -> dict:
	"""A row this layer adds, stored whole so nothing below has to hold it."""
	row = {field: item.get(field) for field in OWN_FIELDS}
	if item["type"] == "Link":
		row["icon"] = item.get("icon")
	row["added"] = 1
	if anchors:
		row["anchors"] = json.dumps(anchors)
	return row


def anchors_for(below: list[dict], desired: list[dict]) -> dict[str, list[dict]]:
	"""One anchor for each item that has to move, and nothing for the ones that keep their order."""
	below_groups = siblings(below)
	anchors: dict[str, list[dict]] = {}

	for parent, keys in siblings(desired).items():
		staying = longest_common(below_groups.get(parent, []), keys)
		for index, key in enumerate(keys):
			if key in staying:
				continue
			if index:
				anchors[key] = [{"after": keys[index - 1]}]
				continue
			# First in its group: anchor before the first item that is not moving itself.
			ahead = next((other for other in keys[1:] if other in staying), None)
			if ahead:
				anchors[key] = [{"before": ahead}]
			elif parent:
				anchors[key] = [{"parent_key": parent}]
	return anchors


def siblings(items: list[dict]) -> dict[str | None, list[str]]:
	groups: dict[str | None, list[str]] = {}
	for item in items:
		groups.setdefault(item.get("parent_key") or None, []).append(item["key"])
	return groups


def longest_common(before: list[str], after: list[str]) -> set[str]:
	"""The largest set of keys that keep their relative order, so the fewest items move."""
	rows, columns = len(before), len(after)
	lengths = [[0] * (columns + 1) for _ in range(rows + 1)]
	for i in range(rows - 1, -1, -1):
		for j in range(columns - 1, -1, -1):
			if before[i] == after[j]:
				lengths[i][j] = lengths[i + 1][j + 1] + 1
			else:
				lengths[i][j] = max(lengths[i + 1][j], lengths[i][j + 1])

	common, i, j = set(), 0, 0
	while i < rows and j < columns:
		if before[i] == after[j]:
			common.add(before[i])
			i, j = i + 1, j + 1
		elif lengths[i + 1][j] >= lengths[i][j + 1]:
			i += 1
		else:
			j += 1
	return common
