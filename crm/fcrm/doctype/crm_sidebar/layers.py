"""Fold sidebar layers over the standard items: hook, then site, then user. Later layers win.

A layer stores overrides, not copies. A row names an item by `key` and sets only the fields
listed in its `overrides`. A move is an anchor ("after row X"), so an item a later release
ships still lands where the hook puts it. Rows a layer added are stored whole.
"""

import json

ITEM_FIELDS = (
	"key",
	"type",
	"label",
	"icon",
	"link_type",
	"link_to",
	"parent_key",
	"collapsible",
	"keep_closed",
	"hidden",
)
OVERRIDABLE = ("label", "icon", "collapsible", "keep_closed", "hidden")
OWN_PREFIXES = ("site:", "user:")


def resolve(base: list[dict], layers: list[list[dict]]) -> list[dict]:
	"""The sidebar these layers make, in the order it draws."""
	items = [as_item(item) for item in base]
	for rows in layers:
		items = apply_layer(items, rows)
	return ordered(items)


def as_item(row: dict) -> dict:
	item = {field: row.get(field) for field in ITEM_FIELDS}
	item["type"] = item["type"] or "Link"
	for field in ("collapsible", "keep_closed", "hidden"):
		item[field] = int(bool(item[field]))
	return item


def apply_layer(items: list[dict], rows: list[dict]) -> list[dict]:
	"""Apply one layer's rows to `items`, then move the rows that carry an anchor."""
	by_key = {item["key"]: item for item in items}
	merged = list(items)
	placed = []

	for row in rows:
		key = row.get("key")
		if key in by_key and row.get("added"):
			# A row is added once; a second row under its key is a stale copy.
			continue
		if key in by_key:
			apply_overrides(by_key[key], row)
		elif row.get("added"):
			by_key[key] = as_item(row)
			merged.append(by_key[key])
		else:
			# The item is gone, such as a built-in page a later release removed.
			continue

		attempts = anchor_attempts(row.get("anchors"))
		if attempts:
			placed.append((by_key[key], attempts))

	return place_by_anchors(merged, placed)


def apply_overrides(item: dict, row: dict):
	for field in parse_list(row.get("overrides")):
		if field in OVERRIDABLE:
			item[field] = row.get(field)


def ordered(items: list[dict]) -> list[dict]:
	"""The main list first, then each section followed by its items.

	Items go only under a section a layer added; any other parent is dropped.
	"""
	sections = [item for item in items if item["type"] == "Section"]
	custom = {item["key"] for item in sections if is_own_key(item["key"])}
	for item in items:
		if item["type"] == "Section" or item.get("parent_key") not in custom:
			item["parent_key"] = None

	result = [item for item in items if item["type"] != "Section" and not item["parent_key"]]
	for section in sections:
		result.append(section)
		result += [item for item in items if item["parent_key"] == section["key"]]
	return result


def is_own_key(key: str | None) -> bool:
	return bool(key) and key.startswith(OWN_PREFIXES)


def parse_list(raw) -> list:
	try:
		value = json.loads(raw) if isinstance(raw, str) else raw
	except ValueError:
		return []
	return value if isinstance(value, list) else []


def anchor_attempts(raw) -> list[dict]:
	"""A row's stored anchors as well-formed attempts; one naming both sides names none."""
	attempts = []
	for anchor in parse_list(raw):
		if not isinstance(anchor, dict):
			continue
		after, before, parent = anchor.get("after"), anchor.get("before"), anchor.get("parent_key")
		if (after and before) or not (after or before or parent):
			continue
		attempts.append({"after": after, "before": before, "parent_key": parent})
	return attempts


def place_by_anchors(items: list[dict], placed: list[tuple[dict, list[dict]]]) -> list[dict]:
	"""Move each row to the first of its anchors that names keys still in the list."""
	present = {item["key"] for item in items}
	anchored: dict[str, str] = {}

	for item, attempts in placed:
		for attempt in attempts:
			target = attempt["after"] or attempt["before"] or attempt["parent_key"]
			names = [attempt[field] for field in ("after", "before", "parent_key") if attempt[field]]
			if all(name in present for name in names) and not leads_back(target, item["key"], anchored):
				place(items, item, attempt)
				anchored[item["key"]] = target
				break

	return items


def leads_back(target: str, key: str, anchored: dict[str, str]) -> bool:
	"""Whether following what each row was anchored to gets back to `key`."""
	seen = set()
	while target and target not in seen:
		if target == key:
			return True
		seen.add(target)
		target = anchored.get(target)
	return False


def place(items: list[dict], item: dict, anchor: dict):
	"""Move `item`, and the items in it when it is a section, to where the anchor says."""
	beside = anchor["after"] or anchor["before"]
	block = [item] + [entry for entry in items if entry.get("parent_key") == item["key"]]
	if any(entry["key"] == (beside or anchor["parent_key"]) for entry in block):
		return

	for entry in block:
		items.remove(entry)

	if beside:
		target = index_of(items, beside)
		parent = anchor["parent_key"] or items[target].get("parent_key")
		at = end_of(items, beside) + 1 if anchor["after"] else target
	else:
		parent = anchor["parent_key"]
		at = end_of(items, parent) + 1

	item["parent_key"] = parent
	items[at:at] = block


def index_of(items: list[dict], key: str) -> int:
	return next(index for index, entry in enumerate(items) if entry["key"] == key)


def end_of(items: list[dict], key: str) -> int:
	"""The index of the last item in `key`'s section, or of `key` itself."""
	inside = [index for index, entry in enumerate(items) if entry.get("parent_key") == key]
	return max([index_of(items, key), *inside])
