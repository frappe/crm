# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Five reference Automation Flows, installable on any CRM site.

	bench --site <site> execute crm.automation.reference_flows.install
	bench --site <site> execute crm.automation.reference_flows.install --kwargs "{'enable': 1}"
	bench --site <site> execute crm.automation.reference_flows.uninstall

They are created disabled by default: two of them send real email to the record's own
address, so turning them on is a deliberate act.
"""

import frappe

TEMPLATES = {
	"CRM Web Lead Welcome": (
		"Thanks for reaching out, {{ doc.first_name }}",
		"<p>Hi {{ doc.first_name }},</p><p>Thanks for getting in touch through our website. "
		"Tell us what you're trying to solve and we'll take it from there.</p>",
	),
	"CRM Outbound Lead Welcome": (
		"Introducing ourselves, {{ doc.first_name }}",
		"<p>Hi {{ doc.first_name }},</p><p>We work with teams like {{ doc.organization }} on "
		"exactly this problem. Worth a short call?</p>",
	),
	"CRM Lead Follow Up": (
		"Following up, {{ doc.first_name }}",
		"<p>Hi {{ doc.first_name }},</p><p>Circling back on my note from a couple of days ago — "
		"still happy to help.</p>",
	),
}


def install(enable: int = 0):
	"""Create (or replace) the reference flows and everything they depend on."""
	ensure_email_templates()
	for build in builders():
		flow = build()
		flow["enabled"] = frappe.utils.cint(enable)
		print("installed:", replace_flow(flow))
	frappe.db.commit()


def uninstall():
	"""Remove the reference flows. The Email Templates are left in place.

	Matched by their exact titles — the flows carry no marker of their own, and a flow a user
	built by hand is not ours to delete.
	"""
	for title in [build()["title"] for build in builders()]:
		name = frappe.db.get_value("Automation Flow", {"title": title}, "name")
		if not name:
			continue
		frappe.delete_doc("Automation Flow", name, force=True, ignore_permissions=True)
		print("removed:", title)
	frappe.db.commit()


def builders() -> tuple:
	return (welcome_sequence, reply_temperature, profile_scoring, qualified_conversion, stalled_deal)


def replace_flow(payload) -> str:
	existing = frappe.db.get_value("Automation Flow", {"title": payload["title"]}, "name")
	if existing:
		frappe.delete_doc("Automation Flow", existing, force=True, ignore_permissions=True)
	return frappe.get_doc(payload).insert(ignore_permissions=True).title


def ensure_email_templates():
	for name, (subject, response) in TEMPLATES.items():
		if frappe.db.exists("Email Template", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": name,
				"subject": subject,
				"response": response,
				"reference_doctype": "CRM Lead",
			}
		).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# 1. Welcome the lead differently by source, then follow up with both after two days.
# ---------------------------------------------------------------------------
def welcome_sequence() -> dict:
	return {
		**flow("Welcome sequence by lead source", "CRM Lead", "Doc Created"),
		"actions": [
			step(1, "by_source", "If", condition='doc.source == "Website"'),
			email_step(2, "welcome_web", "CRM Web Lead Welcome", parent=1, branch="If"),
			email_step(3, "welcome_outbound", "CRM Outbound Lead Welcome", parent=1, branch="Else"),
			step(4, "wait_two_days", "Wait", params={"value": 2, "unit": "Days"}),
			email_step(5, "follow_up", "CRM Lead Follow Up"),
		],
	}


# ---------------------------------------------------------------------------
# 2. We emailed a lead: warm now, hot if they reply within three days, cold if they don't.
# ---------------------------------------------------------------------------
def reply_temperature() -> dict:
	return {
		**flow("Lead temperature from reply", "Communication", "Doc Created"),
		"filters": frappe.as_json(
			[
				["communication_type", "=", "Communication"],
				["sent_or_received", "=", "Sent"],
				["reference_doctype", "=", "CRM Lead"],
			]
		),
		"relationships": frappe.as_json(
			[
				{
					"alias": "lead",
					"source": "trigger",
					"relationship": "reference",
					# `reference` allows a Lead or a Deal; naming which one lets the builder
					# offer the right actions and fields for the alias.
					"target_doctype": "CRM Lead",
				}
			]
		),
		"actions": [
			temperature(1, "mark_warm", "Warm"),
			step(
				2,
				"wait_for_reply",
				"WaitForEvent",
				params={
					"event_name": "crm.prospect_message_received",
					"correlation_key": "{{ doc.message_id or doc.name }}",
					"timeout_value": 3,
					"timeout_unit": "Days",
				},
			),
			step(3, "did_reply", "If", condition=EVENT_MATCHED),
			temperature(4, "mark_hot", "Hot", parent=3, branch="If"),
			score(5, "reply_bonus", 15, "Replied within three days", target="lead", parent=3, branch="If"),
			temperature(6, "mark_cold", "Cold", parent=3, branch="Else"),
			score(
				7, "silence_penalty", -10, "No reply in three days", target="lead", parent=3, branch="Else"
			),
		],
	}


# ---------------------------------------------------------------------------
# 3. Score a new lead on its profile, then band the total into a temperature.
# ---------------------------------------------------------------------------
FREE_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]
SENIOR_TITLES = ["chief", "head", "vp", "vice president", "director", "founder", "owner", "president"]
LARGE_COMPANY_SIZES = ["201-500", "501-1000", "1000+"]
INBOUND_SOURCES = ["Website", "Referral", "Existing Customer"]


def _title_is_senior() -> str:
	"""Written out as an `or` chain: conditions run through `safe_eval`, which has no `any`."""
	return " or ".join(f'"{word}" in (doc.job_title or "").lower()' for word in SENIOR_TITLES)


SIGNALS = [
	(
		"business_email",
		"Work email address",
		f'doc.email and doc.email.split("@")[-1].lower() not in {FREE_EMAIL_DOMAINS}',
		15,
	),
	("named_organization", "Organization is known", '(doc.organization or "") != ""', 10),
	("senior_contact", "Job title looks senior", _title_is_senior(), 15),
	("large_company", "Company is large", f"doc.no_of_employees in {LARGE_COMPANY_SIZES}", 10),
]

HOT_AT = 45
WARM_AT = 25


def profile_scoring() -> dict:
	"""Every signal is its own If, so the run log reads as a scorecard: each step shows what it
	found and what it added. The banding at the end totals the points the run actually awarded."""
	rows, idx = [], 1
	for key, label, condition, points in SIGNALS:
		rows.append(step(idx, key, "If", condition=condition))
		rows.append(score(idx + 1, _points_key(key), points, label, parent=idx, branch="If"))
		idx += 2

	rows += _source_signal(idx)
	rows += _banding(idx + 3)
	return {**flow("Lead scoring from the profile", "CRM Lead", "Doc Created"), "actions": rows}


def _source_signal(idx) -> list[dict]:
	"""The one signal that scores on both arms: an inbound lead is worth more than an outbound one."""
	return [
		step(idx, "inbound_source", "If", condition=f"doc.source in {INBOUND_SOURCES}"),
		score(idx + 1, _points_key("inbound_source"), 20, "Inbound lead", parent=idx, branch="If"),
		score(idx + 2, _points_key("outbound_source"), 5, "Outbound lead", parent=idx, branch="Else"),
	]


def _banding(idx) -> list[dict]:
	return [
		step(idx, "is_hot", "If", condition=_total_at_least(HOT_AT)),
		temperature(idx + 1, "mark_hot", "Hot", target="trigger", parent=idx, branch="If"),
		step(idx + 2, "is_warm", "If", condition=_total_at_least(WARM_AT), parent=idx, branch="Else"),
		temperature(idx + 3, "mark_warm", "Warm", target="trigger", parent=idx + 2, branch="If"),
		temperature(idx + 4, "mark_cold", "Cold", target="trigger", parent=idx + 2, branch="Else"),
	]


def _points_key(key) -> str:
	return f"{key}_points"


def _total_at_least(threshold) -> str:
	"""Sum the deltas the scoring steps reported.

	A step that was skipped leaves nothing behind, so its arm contributes zero — which is why
	this reads the run's own outputs instead of the Lead, whose snapshot was loaded before any
	of these steps wrote to it.
	"""
	keys = [_points_key(signal[0]) for signal in SIGNALS]
	keys += [_points_key("inbound_source"), _points_key("outbound_source")]
	awarded = " + ".join(f'context["steps"].get("{key}", {{}}).get("delta", 0)' for key in keys)
	return f"({awarded}) >= {threshold}"


# ---------------------------------------------------------------------------
# 4. A lead reaching Qualified becomes a Deal, with a kickoff task on the new Deal.
# ---------------------------------------------------------------------------
def qualified_conversion() -> dict:
	return {
		**flow("Qualified lead becomes a deal", "CRM Lead", "Field Value Changed"),
		"trigger_field": "status",
		"to_value": "Qualified",
		"condition": "doc.converted == 0",
		"actions": [
			convert_step(1, "convert"),
			create_task_step(2, "kickoff_task"),
			score(3, "qualified_bonus", 25, "Converted to a deal"),
		],
	}


# ---------------------------------------------------------------------------
# 5. A deal changes stage: chase it, and after three quiet days score its Lead down.
# ---------------------------------------------------------------------------
def stalled_deal() -> dict:
	return {
		**flow("Stalled deal follow-up", "CRM Deal", "Field Value Changed"),
		"trigger_field": "status",
		"relationships": frappe.as_json([{"alias": "lead", "source": "trigger", "relationship": "lead"}]),
		"actions": [
			follow_up_task_step(1, "follow_up_task"),
			step(2, "wait_three_days", "Wait", params={"value": 3, "unit": "Days"}),
			quiet_check_step(3, "still_quiet"),
			score(
				4, "went_quiet", -5, "No reply after the stage change", target="lead", parent=3, branch="If"
			),
			score(
				5,
				"stayed_warm",
				5,
				"Prospect replied after the stage change",
				target="lead",
				parent=3,
				branch="Else",
			),
		],
	}


EVENT_MATCHED = 'context.get("event", {}).get("outcome") == "Matched"'


def flow(title, document_type, trigger_type) -> dict:
	return {
		"doctype": "Automation Flow",
		"title": title,
		"document_type": document_type,
		"trigger_type": trigger_type,
		"enabled": 0,
		"run_as": "Automation User",
		"automation_user": "Administrator",
		"stop_on_error": 1,
	}


def step(idx, key, step_type, params=None, condition=None, parent=0, branch="", **extra) -> dict:
	return {
		"doctype": "Automation Action",
		"idx": idx,
		"step_key": key,
		"step_type": step_type,
		"target": "trigger",
		"params": frappe.as_json(params or {}),
		"step_condition": condition,
		"parent_step": parent,
		"branch": branch,
		**extra,
	}


def action(idx, key, action_type, params, target="trigger", **extra) -> dict:
	row = step(idx, key, "Action", params=params, **extra)
	row.update({"action_type": action_type, "target": target})
	return row


def email_step(idx, key, template, **extra) -> dict:
	return action(idx, key, "SendCRMEmail", {"email_template": template}, **extra)


def temperature(idx, key, value, target="lead", **extra) -> dict:
	return action(idx, key, "SetLeadTemperature", {"temperature": value}, target=target, **extra)


def score(idx, key, amount, reason, target="trigger", **extra) -> dict:
	return action(idx, key, "AdjustLeadScore", {"amount": amount, "reason": reason}, target=target, **extra)


def convert_step(idx, key) -> dict:
	params = {"if_converted": "Return Existing", "deal": forecast_defaults()}
	row = action(idx, key, "ConvertLeadToDeal", params)
	row["output_alias"] = "deal"
	return row


def forecast_defaults() -> dict:
	"""Sites with forecasting on reject a Deal without a value and a closing date, so the
	reference flow seeds placeholders the sales rep is expected to correct."""
	if not frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
		return {}
	return {
		"expected_deal_value": 1,
		"expected_closure_date": frappe.utils.add_months(frappe.utils.nowdate(), 1),
	}


def create_task_step(idx, key) -> dict:
	"""Targets the Deal the previous step produced, so `doc` here is that Deal."""
	values = {
		"title": "Kickoff call — {{ doc.organization or doc.lead_name }}",
		"status": "Todo",
		"priority": "High",
		"assigned_to": "{{ trigger.lead_owner or '' }}",
		"reference_doctype": "CRM Deal",
		"reference_docname": "{{ doc.name }}",
		"due_date": "{{ frappe.utils.add_days(frappe.utils.nowdate(), 2) }}",
	}
	return action(idx, key, "CreateDocument", {"doctype": "CRM Task", "values": values}, target="deal")


def follow_up_task_step(idx, key) -> dict:
	"""Skipped entirely when the Deal already has an open task."""
	values = {
		"title": "Follow up on {{ doc.organization or doc.name }}",
		"status": "Todo",
		"reference_doctype": "CRM Deal",
		"reference_docname": "{{ doc.name }}",
		"due_date": "{{ frappe.utils.add_days(frappe.utils.nowdate(), 3) }}",
	}
	row = action(idx, key, "CreateDocument", {"doctype": "CRM Task", "values": values})
	row["related_condition"] = frappe.as_json(
		{
			"type": "RelatedNotExists",
			"source": "trigger",
			"relationship": "tasks",
			"filters": [["status", "not in", ["Done", "Canceled"]]],
		}
	)
	return row


def quiet_check_step(idx, key) -> dict:
	"""If arm = nothing came back since the run started; Else arm = the prospect replied."""
	row = step(idx, key, "If", condition="True")
	row["related_condition"] = frappe.as_json(
		{
			"type": "RelatedNotExists",
			"source": "trigger",
			"relationship": "communications",
			"filters": [
				["sent_or_received", "=", "Received"],
				["creation", ">", "{{ context.run.creation }}"],
			],
		}
	)
	return row
