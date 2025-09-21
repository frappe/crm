import frappe
from frappe.model.document import Document
from frappe.query_builder import JoinType
from frappe.utils.safe_exec import get_safe_globals
from frappe.utils import now_datetime
from pypika import Criterion

def get_sla(doc: Document) -> Document:
	"""
	Get Service Level Agreement for `doc`

	:param doc: Lead/Deal to use
	:return: Applicable SLA
	"""
	SLA = frappe.qb.DocType("CRM Service Level Agreement")
	Priority = frappe.qb.DocType("CRM Service Level Priority")
	now = now_datetime()
	priority = doc.communication_status
	q = (
		frappe.qb.from_(SLA)
		.select(SLA.name, SLA.condition)
		.where(SLA.apply_on == doc.doctype)
		.where(SLA.enabled == True)
		.where(Criterion.any([SLA.start_date.isnull(), SLA.start_date <= now]))
		.where(Criterion.any([SLA.end_date.isnull(), SLA.end_date >= now]))
	)
	if priority:
		q = (
			q.join(Priority, JoinType.inner)
			.on(Priority.parent == SLA.name)
			.where(Priority.priority == priority)
		)
	sla_list = q.run(as_dict=True)
	res = None

	# move default sla to the end of the list
	for sla in sla_list:
		if sla.get("default") == True:
			sla_list.remove(sla)
			sla_list.append(sla)
			break

	for sla in sla_list:
		cond = sla.get("condition")
		if not cond or frappe.safe_eval(cond, None, get_context(doc)):
			res = sla
			break
	return res

def get_context(d: Document) -> dict:
	"""
	Get safe context for `safe_eval`

	:param doc: `Document` to add in context
	:return: Context with `doc` and safe variables
	"""
	utils = get_safe_globals().get("frappe").get("utils")
	return {
		"doc": d.as_dict(),
		"frappe": frappe._dict(utils=utils),
	}