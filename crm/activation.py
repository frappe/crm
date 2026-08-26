import frappe


def get_site_info(site_info):
	# called via hook
	return {"activation": get_sales_data(site_info)}


def get_sales_data(site_info):
	activation_level = site_info.get("activation", {}).get("activation_level", 0)
	sales_data = site_info.get("activation", {}).get("sales_data", [])
	doctypes = [
		"CRM Lead",
		"CRM Deal",
		"CRM Organization",
		"Contact",
		"CRM Task",
		"FCRM Note",
		"CRM Call Log",
		"CRM Lead Status",
		"CRM Deal Status",
		"CRM Lead Source",
		"CRM Industry",
		"CRM Territory",
		"CRM Lost Reason",
		"CRM Product",
		"CRM Form Script",
		"CRM Fields Layout",
		"CRM View Settings",
	]

	for doctype in doctypes:
		count = frappe.db.count(doctype)
		sales_data.append({doctype: count})

	return {"activation_level": activation_level, "sales_data": sales_data}
