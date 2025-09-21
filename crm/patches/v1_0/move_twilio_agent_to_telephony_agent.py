import frappe


def execute():
	if not frappe.db.exists("DocType", "CRM Telephony Agent"):
		frappe.reload_doctype("CRM Telephony Agent", force=True)

	if frappe.db.exists("DocType", "Twilio Agents") and frappe.db.count("Twilio Agents") == 0:
		return

	agents = frappe.db.sql("SELECT * FROM `tabTwilio Agents`", as_dict=True)
	if agents:
		for agent in agents:
			doc = frappe.get_doc(
				{
					"doctype": "CRM Telephony Agent",
					"creation": agent.get("creation"),
					"modified": agent.get("modified"),
					"modified_by": agent.get("modified_by"),
					"owner": agent.get("owner"),
					"user": agent.get("user"),
					"twilio_number": agent.get("twilio_number"),
					"user_name": agent.get("user_name"),
					"twilio": True,
				}
			)
			doc.db_insert()
