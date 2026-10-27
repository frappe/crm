import frappe


def execute():
	settings = frappe.get_single("ERPNext CRM Settings")
	if not settings.enabled:
		return
	settings.create_custom_fields_in_frappe_crm()
	frappe.enqueue(
		"crm.integrations.erpnext.customers.run_reconciliation",
		queue="long",
		timeout=3600,
		enqueue_after_commit=True,
		job_id="crm_customer_reconciliation",
		deduplicate=True,
		legacy_only=True,
	)
