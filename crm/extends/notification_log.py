import frappe

# CRM doctype -> frontend list route. Records live at /crm/<route>/<name>.
CRM_ROUTES = {
	"CRM Lead": "leads",
	"CRM Deal": "deals",
}


def before_insert(doc, method=None):
	"""Point CRM notification emails at the CRM UI instead of the Desk form.

	Notification Log's email builder uses `doc.link` when set, otherwise it
	falls back to a Desk (`/app/...`) form URL. CRM users often have Desk
	access restricted, so build a CRM frontend link for CRM documents.
	See https://github.com/frappe/crm/issues/705.
	"""
	if doc.link:
		return

	route = get_crm_route(doc.document_type, doc.document_name)
	if route:
		doc.link = frappe.utils.get_url(route)


def get_crm_route(doctype, name):
	"""Frontend path for a CRM record, or None for non-CRM documents.

	Tasks have no standalone page in the CRM UI, so link to their parent
	Lead/Deal's Tasks tab, mirroring the in-app notification behaviour.
	"""
	if not name:
		return None

	suffix = ""
	if doctype == "CRM Task":
		parent = frappe.db.get_value(
			"CRM Task", name, ["reference_doctype", "reference_docname"], as_dict=True
		)
		if not parent or not parent.reference_docname:
			return None
		doctype, name = parent.reference_doctype, parent.reference_docname
		suffix = "#tasks"

	list_route = CRM_ROUTES.get(doctype)
	if not list_route:
		return None

	return f"/crm/{list_route}/{name}{suffix}"
