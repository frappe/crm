from dataclasses import dataclass, field
from typing import Literal

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")
Rule = Literal["already_linked", "exact_code", "no_match"]


@dataclass
class PairAction:
	rule: Rule
	crm_updates: dict = field(default_factory=dict)
	item_updates: dict = field(default_factory=dict)


def classify_pair(item: dict, product: dict) -> PairAction:
	if item.get("crm_product_code") == product.get("name") and product.get("erpnext_item_code") == item.get(
		"item_code"
	):
		return PairAction(rule="already_linked")

	if item.get("item_code") == product.get("product_code"):
		updates = {"erpnext_item_code": item["item_code"]}
		for f in CATALOGUE_FIELDS:
			updates[f] = item.get(f)
		if not product.get("product_name") and item.get("item_name"):
			updates["product_name"] = item["item_name"]
		return PairAction(
			rule="exact_code",
			crm_updates=updates,
			item_updates={"crm_product_code": product["name"]},
		)

	return PairAction(rule="no_match")


def detect_orphan(product: dict, existing_item_codes: set[str]) -> bool:
	linked = product.get("erpnext_item_code")
	return bool(linked) and linked not in existing_item_codes
