import frappe


def execute():
	"""The editor now shows a custom link on its host's row, so a one-host page's own link moves there."""
	for page in frappe.get_all(
		"CRM Booking Page", filters={"location_type": "Custom link"}, fields=["name", "location"]
	):
		link = (page.location or "").strip()
		if not link.lower().startswith(("http://", "https://")):
			continue
		hosts = frappe.get_all(
			"CRM Booking Page Host",
			filters={"parent": page.name, "parenttype": "CRM Booking Page"},
			fields=["name", "meeting_link"],
		)
		if len(hosts) != 1 or hosts[0].meeting_link:
			continue
		frappe.db.set_value(
			"CRM Booking Page Host", hosts[0].name, "meeting_link", link, update_modified=False
		)
		frappe.db.set_value("CRM Booking Page", page.name, "location", "", update_modified=False)
