# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Nine reference Automation Flows, installable on any CRM site.

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
		"<p>Hi {{ doc.first_name }},</p><p>Circling back on my note from a couple of days ago - "
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

	Matched by their exact titles - the flows carry no marker of their own, and a flow a user
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
	return (
		welcome_sequence,
		reply_temperature,
		profile_scoring,
		assign_on_outreach,
		lead_routing,
		engagement_scoring,
		qualified_conversion,
		stalled_deal,
		high_value_deal_watch,
	)


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

	A step that was skipped leaves nothing behind, so its arm contributes zero - which is why
	this reads the run's own outputs instead of the Lead, whose snapshot was loaded before any
	of these steps wrote to it.
	"""
	keys = [_points_key(signal[0]) for signal in SIGNALS]
	keys += [_points_key("inbound_source"), _points_key("outbound_source")]
	awarded = " + ".join(f'context["steps"].get("{key}", {{}}).get("delta", 0)' for key in keys)
	return f"({awarded}) >= {threshold}"


# ---------------------------------------------------------------------------
# 4. Ownership follows the lead: whoever should be on it next gets assigned.
#
# A flow has one trigger, so routing is two flows: one on the outreach itself, one on the
# lead changing. Neither waits, so both land the moment you act in the UI.
# ---------------------------------------------------------------------------
OUTREACH_OWNER = "crm.rep1@example.com"
HOT_LEAD_OWNER = "crm.supervisor@example.com"
QUALIFIED_OWNER = "crm.rep2@example.com"
HOT_SCORE = 50


def assign_on_outreach() -> dict:
	"""We emailed a prospect, so the lead lands on the rep who owns the follow-up."""
	return {
		**flow("Assign the lead when we email it", "Communication", "Doc Created"),
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
					"target_doctype": "CRM Lead",
				}
			]
		),
		"actions": [
			assign_step(1, "assign_outreach_owner", OUTREACH_OWNER, "We emailed this lead", target="lead")
		],
	}


def lead_routing() -> dict:
	"""Two independent checks on every lead update, so one save can fire both."""
	return {
		**flow("Route the lead as it changes", "CRM Lead", "Doc Updated"),
		"actions": [
			step(1, "is_hot", "If", condition=f"doc.lead_score >= {HOT_SCORE}"),
			assign_step(
				2,
				"assign_hot_lead",
				HOT_LEAD_OWNER,
				"Lead score reached {{ doc.lead_score }}",
				parent=1,
				branch="If",
			),
			step(3, "is_qualified", "If", condition='doc.status == "Qualified"'),
			assign_step(4, "assign_qualified", QUALIFIED_OWNER, "Lead is qualified", parent=3, branch="If"),
			email_step(
				5,
				"qualified_email",
				"CRM Lead Follow Up",
				sender=QUALIFIED_OWNER,
				parent=3,
				branch="If",
			),
		],
	}


# ---------------------------------------------------------------------------
# 5. Scoring the lead as it is worked, which is the other half of the profile scoring
# that runs on creation.
# ---------------------------------------------------------------------------
ENGAGEMENT_SIGNALS = [
	("reached_out", "Reached out to the lead", 'doc.status == "Contacted"', 5),
	("nurturing", "Lead moved to nurture", 'doc.status == "Nurture"', 10),
	("qualified", "Lead qualified", 'doc.status == "Qualified"', 20),
	("went_cold", "Lead was disqualified", 'doc.status in ["Unqualified", "Junk"]', -30),
]


def engagement_scoring() -> dict:
	"""Scores each move through the pipeline, and bands the running total afterwards.

	Triggered on the status field changing rather than on any update: a plain update fires on
	every save, so a signal like this would add its points again each time the record is
	touched. A field change fires once per actual transition.
	"""
	rows, idx = [], 1
	for key, label, condition, points in ENGAGEMENT_SIGNALS:
		rows.append(step(idx, key, "If", condition=condition))
		rows.append(score(idx + 1, _points_key(key), points, label, parent=idx, branch="If"))
		idx += 2
	rows += _engagement_banding(idx)
	return {
		**flow("Score the lead as it is worked", "CRM Lead", "Field Value Changed"),
		"trigger_field": "status",
		"actions": rows,
	}


def _engagement_banding(idx) -> list[dict]:
	"""Bands on the score the Lead now carries, not on this run's points, because the score
	has been built up by earlier runs too."""
	return [
		step(idx, "now_hot", "If", condition=f"doc.lead_score >= {HOT_SCORE}"),
		temperature(idx + 1, "engagement_hot", "Hot", target="trigger", parent=idx, branch="If"),
		step(idx + 2, "now_warm", "If", condition="doc.lead_score >= 20", parent=idx, branch="Else"),
		temperature(idx + 3, "engagement_warm", "Warm", target="trigger", parent=idx + 2, branch="If"),
		temperature(idx + 4, "engagement_cold", "Cold", target="trigger", parent=idx + 2, branch="Else"),
	]


# ---------------------------------------------------------------------------
# 6. A lead reaching Qualified becomes a Deal, with a kickoff task on the new Deal.
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
# 7. A deal changes stage: chase it, and after three quiet days score its Lead down.
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


# ---------------------------------------------------------------------------
# 9. A high value deal moves: route it by confidence, then check three days later
# whether anyone actually came back.
# ---------------------------------------------------------------------------
HIGH_VALUE_AT = 50000
COMMIT_PROBABILITY = 70
QUIET_DAYS = 3


def high_value_deal_watch() -> dict:
	"""The whole flow is gated on deal value, so small deals never start a run at all.

	Confidence decides who picks it up: a deal the rep expects to close needs a close plan,
	one they do not needs pressure testing. Either way the wait and the silence check that
	follow are the same, which is why they sit outside the arms.
	"""
	return {
		**flow("High value deal watch", "CRM Deal", "Doc Updated"),
		"condition": f"(doc.expected_deal_value or 0) >= {HIGH_VALUE_AT}",
		"actions": [
			step(1, "is_committing", "If", condition=f"(doc.probability or 0) >= {COMMIT_PROBABILITY}"),
			assign_step(
				2,
				"assign_closer",
				QUALIFIED_OWNER,
				"High value deal at {{ doc.probability }}% - build the close plan",
				parent=1,
				branch="If",
			),
			deal_task_step(
				3,
				"close_plan",
				"Build the close plan for {{ doc.organization or doc.name }}",
				days=2,
				parent=1,
				branch="If",
			),
			assign_step(
				4,
				"assign_reviewer",
				HOT_LEAD_OWNER,
				"High value deal still at {{ doc.probability }}% - needs a second look",
				parent=1,
				branch="Else",
			),
			deal_task_step(
				5,
				"pressure_test",
				"Pressure test {{ doc.organization or doc.name }}",
				days=1,
				parent=1,
				branch="Else",
			),
			notify_step(
				6,
				"alert_desk",
				"System",
				[HOT_LEAD_OWNER],
				"High value deal moved: {{ doc.organization or doc.name }}",
				"<p>{{ doc.organization or doc.name }} is at {{ doc.expected_deal_value }} "
				"and {{ doc.probability }}% confidence, closing {{ doc.expected_closure_date }}.</p>",
			),
			step(7, "wait_for_movement", "Wait", params={"value": QUIET_DAYS, "unit": "Days"}),
			quiet_check_step(8, "nobody_replied"),
			notify_step(
				9,
				"escalate",
				"Email",
				[HOT_LEAD_OWNER],
				"No contact in {0} days: {{{{ doc.organization or doc.name }}}}".format(QUIET_DAYS),
				"<p>Nothing has come back on a deal worth {{ doc.expected_deal_value }}. "
				"It is worth a call before the close date.</p>",
				parent=8,
				branch="If",
			),
			# Everything here stays on the Deal: a Deal created directly has no originating
			# Lead, and an unresolvable alias fails the run before step one.
			nudge_step(10, "confidence_drops", "probability", -10, parent=8, branch="If"),
			deal_task_step(
				11,
				"rescue_call",
				"Call {{ doc.organization or doc.name }} - no contact in {0} days".format(QUIET_DAYS),
				days=0,
				parent=8,
				branch="If",
			),
			nudge_step(12, "confidence_holds", "probability", 5, parent=8, branch="Else"),
		],
	}


def notify_step(idx, key, channel, recipients, subject, message, **extra) -> dict:
	return action(
		idx,
		key,
		"SendNotification",
		{"channel": channel, "recipients": recipients, "subject": subject, "message": message},
		**extra,
	)


def nudge_step(idx, key, field, amount, **extra) -> dict:
	return action(idx, key, "IncrementFieldValue", {"field": field, "amount": amount}, **extra)


def deal_task_step(idx, key, title, days, **extra) -> dict:
	values = {
		"title": title,
		"status": "Todo",
		"priority": "High",
		"assigned_to": "{{ doc.deal_owner or '' }}",
		"reference_doctype": "CRM Deal",
		"reference_docname": "{{ doc.name }}",
		"due_date": f"{{{{ frappe.utils.add_days(frappe.utils.nowdate(), {days}) }}}}",
	}
	return action(idx, key, "CreateDocument", {"doctype": "CRM Task", "values": values}, **extra)


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


def email_step(idx, key, template, sender=None, **extra) -> dict:
	params = {"email_template": template}
	if sender:
		params["sender"] = sender
	return action(idx, key, "SendCRMEmail", params, **extra)


def assign_step(idx, key, user, description, target="trigger", **extra) -> dict:
	return action(
		idx,
		key,
		"AssignToUser",
		{"assign_to": [user], "description": description},
		target=target,
		**extra,
	)


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
		"title": "Kickoff call - {{ doc.organization or doc.lead_name }}",
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
