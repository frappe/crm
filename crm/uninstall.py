# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
import click
import frappe


def before_uninstall():
	delete_email_template_custom_fields()
	delete_app_form_layouts()


def delete_email_template_custom_fields():
	if frappe.get_meta("Email Template").has_field("enabled"):
		click.secho("* Uninstalling Custom Fields from Email Template")

		fieldnames = (
			"enabled",
			"reference_doctype",
		)

		for fieldname in fieldnames:
			frappe.db.delete("Custom Field", {"name": "Email Template-" + fieldname})

		frappe.clear_cache(doctype="Email Template")


def delete_app_form_layouts():
	# Form Layout refuses to save a row naming an app that is not installed.
	frappe.db.delete("Form Layout", {"app": "crm"})
