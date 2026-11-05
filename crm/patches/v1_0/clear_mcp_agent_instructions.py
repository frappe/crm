import frappe

# Text that crm.patches.v1_0.set_mcp_agent_instructions wrote. Agent guidance now ships as skills/frappe-crm.
SEEDED_AGENT_INSTRUCTIONS = """Frappe CRM tracks sales in CRM Lead (unqualified prospects) and CRM Deal (qualified opportunities).
- Convert a lead with call_method crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal, args {"lead": "<name>"}. Do not create a CRM Deal from lead data yourself.
- Valid statuses are the records in CRM Lead Status and CRM Deal Status. Their type field (Open, Ongoing, On Hold, Won, Lost) gives the meaning.
- Notes are FCRM Note and tasks are CRM Task. Link both to a lead or deal through reference_doctype and reference_docname.
- Get a lead's or deal's timeline with call_method crm.api.activities.get_activities, args {"name": "<lead or deal name>"}.
- Deal contacts live in the contacts table. Change them with add_contact, remove_contact and set_primary_contact in crm.fcrm.doctype.crm_deal.crm_deal.
- Organizations are CRM Organization. People are Contact."""


def execute():
	if not frappe.db.exists("DocType", "MCP Settings"):
		return
	if frappe.db.get_single_value("MCP Settings", "agent_instructions") == SEEDED_AGENT_INSTRUCTIONS:
		frappe.db.set_single_value("MCP Settings", "agent_instructions", "")
