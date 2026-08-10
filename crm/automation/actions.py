# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""CRM automation actions.

Registered through the `automation_actions` hook. Each one delegates to CRM domain logic -
the engine only supplies the resolved target document and the step's params.
"""

from typing import ClassVar

import frappe
from frappe import _
from frappe.automation_engine.actions.base import AutomationAction, AutomationParamError

from crm.automation.scoring import adjust_lead_score, set_lead_temperature, temperature_options
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal, existing_deal


def require_doctype(doctype, allowed, label):
	"""`applicable_doctypes` only filters by the flow's DocType - a step aimed at a record
	alias has to be checked against that alias' DocType, at save time and again at run time."""
	if doctype and doctype not in allowed:
		raise AutomationParamError(
			_("{0} must act on {1}, not {2}").format(label, " or ".join(allowed), doctype),
			fieldname="target",
		)


class AdjustLeadScore(AutomationAction):
	action_type = "AdjustLeadScore"
	label = "Adjust Lead Score"
	description = "Add to or subtract from a Lead's score, with an audited reason."
	applicable_doctypes: ClassVar[list] = ["CRM Lead"]
	output_schema: ClassVar[dict] = {
		"old_value": {"fieldtype": "Int"},
		"new_value": {"fieldtype": "Int"},
		"delta": {"fieldtype": "Int"},
	}
	params_schema: ClassVar[list] = [
		{"fieldname": "amount", "label": "Amount", "fieldtype": "Int", "reqd": 1},
		{"fieldname": "reason", "label": "Reason", "fieldtype": "Data"},
		{"fieldname": "min_score", "label": "Minimum Score", "fieldtype": "Int"},
		{"fieldname": "max_score", "label": "Maximum Score", "fieldtype": "Int"},
	]

	def validate(self, params, doctype):
		require_doctype(doctype, ["CRM Lead"], self.label)
		if not params.get("amount"):
			raise AutomationParamError(_("Amount is required"), fieldname="amount")
		bounds = (params.get("min_score"), params.get("max_score"))
		if all(bound not in (None, "") for bound in bounds) and int(bounds[0]) > int(bounds[1]):
			raise AutomationParamError(_("Minimum score is above the maximum"), fieldname="min_score")

	def execute(self, doc, params, context):
		require_doctype(doc and doc.doctype, ["CRM Lead"], self.label)
		return adjust_lead_score(
			doc,
			params["amount"],
			reason=params.get("reason"),
			min_score=params.get("min_score"),
			max_score=params.get("max_score"),
		)


class SetLeadTemperature(AutomationAction):
	action_type = "SetLeadTemperature"
	label = "Set Lead Temperature"
	description = "Mark a Lead Cold, Warm or Hot."
	applicable_doctypes: ClassVar[list] = ["CRM Lead"]
	output_schema: ClassVar[dict] = {"old_value": {"fieldtype": "Data"}, "new_value": {"fieldtype": "Data"}}
	params_schema: ClassVar[list] = [
		{
			"fieldname": "temperature",
			"label": "Temperature",
			"fieldtype": "Select",
			"options": "Cold\nWarm\nHot",
			"reqd": 1,
		}
	]

	def validate(self, params, doctype):
		require_doctype(doctype, ["CRM Lead"], self.label)
		if params.get("temperature") not in temperature_options():
			raise AutomationParamError(_("Choose a lead temperature"), fieldname="temperature")

	def execute(self, doc, params, context):
		require_doctype(doc and doc.doctype, ["CRM Lead"], self.label)
		return set_lead_temperature(doc, params["temperature"])


class ConvertLeadToDeal(AutomationAction):
	action_type = "ConvertLeadToDeal"
	label = "Convert Lead to Deal"
	description = "Convert a qualified Lead into a Deal using the CRM's own conversion logic."
	applicable_doctypes: ClassVar[list] = ["CRM Lead"]
	output_schema: ClassVar[dict] = {
		"destination_reference": {"doctype": "CRM Deal", "cardinality": "one"},
		"contact": {"doctype": "Contact"},
		"organization": {"doctype": "CRM Organization"},
	}
	params_schema: ClassVar[list] = [
		{
			"fieldname": "if_converted",
			"label": "If Already Converted",
			"fieldtype": "Select",
			"options": "Return Existing\nFail",
			"default": "Return Existing",
		},
		{
			"fieldname": "existing_contact",
			"label": "Existing Contact",
			"fieldtype": "Link",
			"options": "Contact",
		},
		{
			"fieldname": "existing_organization",
			"label": "Existing Organization",
			"fieldtype": "Link",
			"options": "CRM Organization",
		},
		{"fieldname": "deal", "label": "Deal Field Overrides", "fieldtype": "JSON"},
	]

	def validate(self, params, doctype):
		require_doctype(doctype, ["CRM Lead"], self.label)
		if params.get("if_converted") not in (None, "", "Return Existing", "Fail"):
			raise AutomationParamError(_("Unsupported conversion policy"), fieldname="if_converted")

	def output_doctype(self, params):
		return "CRM Deal"

	def execute(self, doc, params, context):
		require_doctype(doc and doc.doctype, ["CRM Lead"], self.label)
		reused = existing_deal(doc.name)
		deal = convert_to_deal(
			doc.name,
			deal=params.get("deal"),
			existing_contact=params.get("existing_contact"),
			existing_organization=params.get("existing_organization"),
			if_converted=params.get("if_converted") or "Return Existing",
		)
		return self._result(doc, deal, reused)

	def _result(self, lead, deal, reused) -> dict:
		deal_doc = frappe.get_doc("CRM Deal", deal)
		return {
			"detail": _("Reused Deal {0}").format(deal) if reused else _("Created Deal {0}").format(deal),
			"destination_reference": {"doctype": "CRM Deal", "name": deal},
			"contact": deal_doc.contacts[0].contact if deal_doc.contacts else None,
			"organization": deal_doc.organization,
			"reused": bool(reused),
		}


class SendEmailToRecord(AutomationAction):
	action_type = "SendCRMEmail"
	label = "Email the Lead or Deal"
	description = "Send an email to the record's own address and log it on its timeline."
	applicable_doctypes: ClassVar[list] = ["CRM Lead", "CRM Deal"]
	output_schema: ClassVar[dict] = {"communication": {"doctype": "Communication"}}
	params_schema: ClassVar[list] = [
		{
			"fieldname": "email_template",
			"label": "Email Template",
			"fieldtype": "Link",
			"options": "Email Template",
		},
		{"fieldname": "subject", "label": "Subject", "fieldtype": "Data"},
		{"fieldname": "message", "label": "Message", "fieldtype": "Text Editor"},
		{
			"fieldname": "sender",
			"label": "Send As",
			"fieldtype": "Link",
			"options": "User",
			"description": "Leave empty to send from the default outgoing account.",
		},
	]

	def validate(self, params, doctype):
		require_doctype(doctype, self.applicable_doctypes, self.label)
		if not (params.get("email_template") or params.get("subject")):
			raise AutomationParamError(_("Pick a template or write a subject"), fieldname="email_template")
		if params.get("email_template") and not frappe.db.exists("Email Template", params["email_template"]):
			raise AutomationParamError(_("Unknown Email Template"), fieldname="email_template")

	def execute(self, doc, params, context):
		from frappe.core.doctype.communication.email import make

		require_doctype(doc and doc.doctype, self.applicable_doctypes, self.label)
		recipient = doc.get("email") if doc else None
		if not recipient:
			raise AutomationParamError(_("{0} has no email address").format(doc.doctype if doc else ""))
		subject, message = self._content(doc, params)
		sender = params.get("sender")
		sent = make(
			doctype=doc.doctype,
			name=doc.name,
			subject=subject,
			content=message,
			recipients=recipient,
			communication_type="Communication",
			send_email=True,
			sender=sender or None,
			sender_full_name=frappe.db.get_value("User", sender, "full_name") if sender else None,
		)
		return {
			"detail": _("Emailed {0}: {1}").format(recipient, subject),
			"communication": sent.get("name"),
			"recipient": recipient,
			"sender": sender,
		}

	def _content(self, doc, params):
		if not params.get("email_template"):
			return params.get("subject"), params.get("message") or ""
		# Rendered against `doc` so templates read the same `{{ doc.field }}` way they do
		# everywhere else in Frappe.
		template = frappe.get_doc("Email Template", params["email_template"])
		context = {"doc": doc, "target": doc}
		body = template.response_html if template.use_html else template.response
		return (
			frappe.render_template(template.subject, context),
			frappe.render_template(body or "", context),
		)


CRM_ACTIONS = [AdjustLeadScore, SetLeadTemperature, ConvertLeadToDeal, SendEmailToRecord]
