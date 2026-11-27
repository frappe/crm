import frappe


def execute():
	"""Put Customize sidebar in the App menu, right after the site's Settings row.

	`after_migrate` would add it at its hook index, which is not after Settings on a site
	that reordered its menu.
	"""
	settings = frappe.get_single("FCRM Settings")
	rows = settings.dropdown_items
	if not rows or any(row.name1 == "customize_sidebar" for row in rows):
		return

	item = next(
		item for item in frappe.get_hooks("standard_dropdown_items") if item["name1"] == "customize_sidebar"
	)
	after = next((row for row in rows if row.is_standard and row.name1 == "settings"), None)
	settings.append("dropdown_items", item, rows.index(after) + 1 if after else len(rows))
	settings.save()
