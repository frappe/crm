"""Seed the follow up reminder settings on existing sites.

The defaults declared on the FCRM Settings fields only apply when the Single is
first created. A site that already has an FCRM Settings row gets NULL/0 for the
newly added fields instead -- which would leave reminders switched off, and the
lead time at 0, on every existing install.

``follow_up_reminder_interval`` is the sentinel for "never configured": it is a
Select with no falsy value of its own, so unlike the two Check fields it can't
be confused with a deliberate opt-out. If it is already set, an admin has been
here and we leave everything alone.

Enabling by default is safe: nothing fires until someone sets a
``next_follow_up`` on a lead or deal, and that field ships empty.
"""

import frappe

DEFAULTS = {
	"enable_follow_up_reminders": 1,
	"follow_up_reminder_before": 30,
	"follow_up_reminder_interval": "minutes",
}


def execute():
	if not frappe.db.exists("DocType", "FCRM Settings"):
		return

	if frappe.db.get_single_value("FCRM Settings", "follow_up_reminder_interval"):
		return

	for field, value in DEFAULTS.items():
		frappe.db.set_single_value("FCRM Settings", field, value)
