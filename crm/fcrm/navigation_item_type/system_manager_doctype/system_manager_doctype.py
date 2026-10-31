# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""The server half of the `System Manager DocType` navigation item kind: a doctype's list that
only a System Manager is offered, though other roles may read the doctype (CRM Form Script)."""

from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from frappe.shell.navigation_filter import NavigationContext


def can_see(items: list[dict], context: "NavigationContext") -> list[dict]:
	return items if "System Manager" in frappe.get_roles(context.user) else []
