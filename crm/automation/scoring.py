# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Lead scoring and temperature policy.

Both write with `db_set` under a row lock: two workers scoring the same Lead serialize
instead of writing from the same stale value, and neither is blocked by unrelated mandatory
fields the way a full document save would be.
"""

import frappe
from frappe import _
from frappe.utils import cint

SCORE_FIELD = "lead_score"
TEMPERATURE_FIELD = "lead_temperature"


def adjust_lead_score(lead, amount, reason=None, min_score=None, max_score=None) -> dict:
	"""Add `amount` to the Lead's score, clamped to the given bounds. Returns the change."""
	lead.check_permission("write")
	_lock(lead)
	lead.reload()
	old_value = cint(lead.get(SCORE_FIELD))
	new_value = _clamp(old_value + cint(amount), min_score, max_score)
	if new_value != old_value:
		lead.db_set(SCORE_FIELD, new_value, update_modified=False)
	return {
		"detail": _("Lead score {0} → {1}{2}").format(old_value, new_value, f" ({reason})" if reason else ""),
		"old_value": old_value,
		"new_value": new_value,
		"delta": new_value - old_value,
		"reason": reason,
	}


def set_lead_temperature(lead, value) -> dict:
	"""Move the Lead between Cold / Warm / Hot. Returns the change."""
	lead.check_permission("write")
	options = temperature_options()
	if value not in options:
		frappe.throw(_("Lead temperature must be one of {0}").format(", ".join(options)))
	old_value = lead.get(TEMPERATURE_FIELD)
	if value != old_value:
		lead.db_set(TEMPERATURE_FIELD, value, update_modified=False)
	return {
		"detail": _("Lead is now {0}").format(value),
		"old_value": old_value,
		"new_value": value,
	}


def temperature_options() -> list[str]:
	field = frappe.get_meta("CRM Lead").get_field(TEMPERATURE_FIELD)
	return [option for option in (field.options or "").split("\n") if option]


def _clamp(value, min_score, max_score) -> int:
	if min_score not in (None, ""):
		value = max(value, cint(min_score))
	if max_score not in (None, ""):
		value = min(value, cint(max_score))
	return value


def _lock(lead):
	table = frappe.qb.DocType(lead.doctype)
	frappe.qb.from_(table).select(table.name).where(table.name == lead.name).for_update().run()
