import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.utils import add_or_remove_lost_reason_section_in_sidepanel


class CRMPipelineEntity:
	"""Mixin for shared Lead/Deal pipeline behavior."""

	_status_doctype: str = ""  # "CRM Lead Status" or "CRM Deal Status"
	_entity_label: str = ""    # "lead" or "deal"

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					return

		assign({"assign_to": [agent], "doctype": self.doctype, "name": self.name}, ignore_permissions=True)

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(
					self.doctype,
					self.name,
					user,
					flags={"ignore_share_permission": True, "ignore_permissions": True},
				)

	def set_sla(self):
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def validate_lost_reason(self):
		if self.status and frappe.get_cached_value(self._status_doctype, self.status, "type") == "Lost":
			if not self.lost_reason:
				frappe.throw(
					_("Please specify a reason for losing the {0}.").format(self._entity_label),
					frappe.ValidationError,
				)
			elif self.lost_reason == "Other" and not self.lost_notes:
				frappe.throw(
					_("Please specify the reason for losing the {0}.").format(self._entity_label),
					frappe.ValidationError,
				)
		if self.has_value_changed("status"):
			add_or_remove_lost_reason_section_in_sidepanel(self)
