import frappe


def execute():
	"""link or create CRM Products for existing ERPNext Items.
	Skipped when ERPNext is not installed, integration is disabled
	"""
	if not frappe.db.exists("DocType", "Item"):
		return

	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled or settings.is_erpnext_in_different_site:
		return

	has_reverse_link = frappe.db.has_column("Item", "crm_product_code")
	fields = ["item_code", "item_name", "standard_rate", "image", "disabled", "description"]
	if has_reverse_link:
		fields.append("crm_product_code")

	created = updated = 0
	for item in frappe.db.get_all("Item", fields=fields):
		target = _find_existing_crm_product(item, has_reverse_link)
		data = {
			"product_name": item["item_name"],
			"standard_rate": item["standard_rate"],
			"image": item["image"],
			"disabled": item["disabled"],
			"description": item["description"],
			"erpnext_item_code": item["item_code"],
		}
		if target:
			frappe.db.set_value("CRM Product", target, data)
			updated += 1
		else:
			product = frappe.new_doc("CRM Product")
			product.product_code = item["item_code"]
			product.update(data)
			product.flags.ignore_erpnext_sync = True
			product.insert(ignore_permissions=True)
			created += 1

	print(f"[sync_existing_items_to_crm_products] {updated} updated, {created} created")


def _find_existing_crm_product(item, has_reverse_link):
	if has_reverse_link and item.get("crm_product_code"):
		if frappe.db.exists("CRM Product", item["crm_product_code"]):
			return item["crm_product_code"]
	linked = frappe.db.get_value("CRM Product", {"erpnext_item_code": item["item_code"]})
	if linked:
		return linked
	if frappe.db.exists("CRM Product", item["item_code"]):
		return item["item_code"]
	return None
