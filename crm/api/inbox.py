import frappe

from crm.api.whatsapp import ALLOWED_WHATSAPP_ROLES


@frappe.whitelist()
def get_conversations(limit: int = 50) -> list[dict]:
	"""Latest message per lead/deal across SMS and WhatsApp, newest first.

	Powers the unified Inbox page: one row per record, with the channel and
	snippet of its most recent message. Clicking a row navigates to the record's
	SMS/WhatsApp tab.
	"""
	if not any(role in ALLOWED_WHATSAPP_ROLES for role in frappe.get_roles()):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	limit = min(int(limit), 200)
	conversations: dict[tuple[str, str], dict] = {}

	def collect(rows, channel):
		for row in rows:
			key = (row.reference_doctype, row.reference_name)
			current = conversations.get(key)
			if not current or row.creation > current["creation"]:
				conversations[key] = {
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"channel": channel,
					"message": row.message or "",
					"type": row.type,
					"creation": row.creation,
				}

	collect(
		frappe.get_all(
			"CRM SMS Message",
			filters={"reference_doctype": ["in", ["CRM Lead", "CRM Deal"]], "reference_name": ["is", "set"]},
			fields=["reference_doctype", "reference_name", "message", "type", "creation"],
			order_by="creation desc",
			limit=limit * 3,
		),
		"SMS",
	)

	if frappe.db.exists("DocType", "WhatsApp Message"):
		collect(
			frappe.get_all(
				"WhatsApp Message",
				filters={
					"reference_doctype": ["in", ["CRM Lead", "CRM Deal"]],
					"reference_name": ["is", "set"],
				},
				fields=["reference_doctype", "reference_name", "message", "type", "creation"],
				order_by="creation desc",
				limit=limit * 3,
			),
			"WhatsApp",
		)

	rows = sorted(conversations.values(), key=lambda c: c["creation"], reverse=True)[:limit]

	# resolve display names in bulk
	lead_names = [r["reference_name"] for r in rows if r["reference_doctype"] == "CRM Lead"]
	deal_names = [r["reference_name"] for r in rows if r["reference_doctype"] == "CRM Deal"]
	leads = {
		d.name: d
		for d in frappe.get_all(
			"CRM Lead",
			filters={"name": ["in", lead_names]},
			fields=["name", "lead_name", "image", "mobile_no"],
		)
	}
	deals = {
		d.name: d
		for d in frappe.get_all(
			"CRM Deal",
			filters={"name": ["in", deal_names]},
			fields=["name", "organization", "mobile_no"],
		)
	}
	for row in rows:
		if row["reference_doctype"] == "CRM Lead":
			info = leads.get(row["reference_name"], {})
			row["title"] = info.get("lead_name") or row["reference_name"]
			row["image"] = info.get("image")
			row["number"] = info.get("mobile_no")
		else:
			info = deals.get(row["reference_name"], {})
			row["title"] = info.get("organization") or row["reference_name"]
			row["image"] = None
			row["number"] = info.get("mobile_no")
	return rows
