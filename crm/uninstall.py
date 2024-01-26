# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import click
import frappe

def before_uninstall():
	delete_email_template_custom_fields()

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