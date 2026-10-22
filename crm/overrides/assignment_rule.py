from frappe.automation.doctype.assignment_rule.assignment_rule import AssignmentRule

from crm.api.availability import get_user_categories

CRM_DOCTYPES = ("CRM Lead", "CRM Deal")
USER_POOL_FIELDS = {
	"Round Robin": "users",
	"Load Balancing": "users",
	"Weighted Distribution": "weighted_users",
}


class CRMAssignmentRule:
	"""Assign leads and deals to Active users first, then Away, then anyone in the rule."""

	def get_user(self, doc):
		fieldname = USER_POOL_FIELDS.get(self.rule)
		if self.document_type not in CRM_DOCTYPES or not fieldname:
			return super().get_user(doc)

		pool = getattr(self, fieldname)
		categories = get_user_categories([row.user for row in pool if row.user])
		active = [row for row in pool if categories.get(row.user) == "Active"]
		reachable = [row for row in pool if categories.get(row.user) in ("Active", "Away")]

		setattr(self, fieldname, active or reachable or pool)
		try:
			return super().get_user(doc)
		finally:
			setattr(self, fieldname, pool)


class CRMAssignmentRuleV15(CRMAssignmentRule, AssignmentRule):
	pass
