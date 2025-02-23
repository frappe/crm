# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import click
import frappe

def before_uninstall():
	delete_email_template_custom_fields()
	delete_email_template_permissions()

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

def delete_email_template_permissions():
	"""Remove Email Template permissions for Sales Manager role"""
	if frappe.db.exists("DocPerm", {"parent": "Email Template", "role": "Sales Manager"}):
		click.secho("* Removing Email Template permissions for Sales Manager")
		frappe.db.delete("DocPerm", {"parent": "Email Template", "role": "Sales Manager"})
		frappe.db.commit()