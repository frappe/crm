# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Manager-only Home widgets, run on a Team scope."""

import json

from crm.fcrm.doctype.crm_dashboard.home_widgets import RECORD_TYPES, RepliesWaiting


class TeamRepliesWaiting(RepliesWaiting):
	def fields(self, doctype: str, table) -> list:
		owner = table[RECORD_TYPES[doctype].owner_field].as_("owner")
		return [*super().fields(doctype, table), owner, table._assign]

	def decorate(self, rows: list) -> list:
		set_owners(rows)
		return super().decorate(rows)


TEAM_WIDGET_DATA = {
	"team_replies_waiting": TeamRepliesWaiting,
}


def set_owners(rows: list):
	"""Fall back to the first assignee for records without an owner."""
	for row in rows:
		assigned = json.loads(row.pop("_assign") or "[]")
		row["owner"] = row["owner"] or next(iter(assigned), None)
