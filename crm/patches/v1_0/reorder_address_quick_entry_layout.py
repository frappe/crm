import json

import frappe

OLD_FIELDS = [
	"address_title",
	"address_type",
	"address_line1",
	"address_line2",
	"city",
	"state",
	"country",
	"pincode",
]

NEW_LAYOUT = [
	{
		"name": "details_section",
		"columns": [
			{
				"name": "column_uSSG",
				"fields": ["address_title", "address_type", "address_line1", "address_line2"],
			}
		],
	},
	{
		"name": "location_section",
		"hideBorder": True,
		"columns": [
			{"name": "column_TCoZ", "fields": ["city", "state"]},
			{"name": "column_PqrK", "fields": ["country", "pincode"]},
		],
	},
]


def execute():
	if not frappe.db.exists("CRM Fields Layout", "Address-Quick Entry"):
		return

	layout = frappe.db.get_value("CRM Fields Layout", "Address-Quick Entry", "layout")
	if not layout:
		return

	parsed = json.loads(layout)

	# Only replace the layout if it's still the untouched default (single
	# section/column with the original field order) — a site that has already
	# customized this Quick Entry should keep its own arrangement.
	is_default = (
		isinstance(parsed, list)
		and len(parsed) == 1
		and len(parsed[0].get("columns", [])) == 1
		and parsed[0]["columns"][0].get("fields") == OLD_FIELDS
	)
	if not is_default:
		return

	frappe.db.set_value("CRM Fields Layout", "Address-Quick Entry", "layout", json.dumps(NEW_LAYOUT))
