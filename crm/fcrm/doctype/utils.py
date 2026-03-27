import json

import frappe


def add_or_remove_lost_reason_section_in_sidepanel(doc):
	doctype = doc.doctype
	if doctype not in ("CRM Deal", "CRM Lead"):
		return

	status_doctype = "CRM Deal Status" if doctype == "CRM Deal" else "CRM Lead Status"

	status = None
	if getattr(doc, "status", None):
		status = frappe.db.get_value(status_doctype, doc.status, "type")
	is_lost = status and status == "Lost"

	layout_doc = frappe.get_doc("CRM Fields Layout", f"{doctype}-Side Panel")
	sections = json.loads(layout_doc.layout)

	lost_reason_section = {
		"name": "lost_reason_section",
		"label": "Lost Reason",
		"opened": True,
		"columns": [
			{
				"name": "lost_reason_column",
				"fields": ["lost_reason", "lost_notes"],
			}
		],
	}

	section_exists = any(section.get("name") == "lost_reason_section" for section in sections)

	if is_lost and not section_exists:
		if sections and sections[0].get("name") == "contacts_section":
			sections = [*sections[:1], lost_reason_section, *sections[1:]]
		else:
			sections = [lost_reason_section, *sections]
		layout_doc.layout = json.dumps(sections)
		layout_doc.save(ignore_permissions=True)
	elif not is_lost and section_exists:
		sections = [section for section in sections if section.get("name") != "lost_reason_section"]
		layout_doc.layout = json.dumps(sections)
		layout_doc.save(ignore_permissions=True)
