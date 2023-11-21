import frappe
from frappe import _
from pypika import Criterion


@frappe.whitelist()
def get_lead(name):
	Lead = frappe.qb.DocType("CRM Lead")

	query = frappe.qb.from_(Lead).select("*").where(Lead.name == name).limit(1)

	lead = query.run(as_dict=True)
	if not len(lead):
		frappe.throw(_("Lead not found"), frappe.DoesNotExistError)
	lead = lead.pop()

	return lead

@frappe.whitelist()
def get_lead_fields():
	DocField = frappe.qb.DocType("DocField")
	CustomField = frappe.qb.DocType("Custom Field")
	not_allowed_fieldtypes = [
		"Section Break",
		"Column Break",
	]
	restricted_fieldnames = [
		"converted",
		"lead_owner",
		"status",
		"image",
		"naming_series"
	]

	fields = (
		frappe.qb.from_(DocField)
		.select(
			DocField.fieldname,
			DocField.fieldtype,
			DocField.label,
			DocField.name,
			DocField.options,
			DocField.read_only,
			DocField.idx,
		)
		.where(DocField.parent == "CRM Lead")
		.where(DocField.hidden == False)
		.where(Criterion.notin(DocField.fieldtype, not_allowed_fieldtypes))
		.where(Criterion.notin(DocField.fieldname, restricted_fieldnames))
		.orderby(DocField.idx)
		.run(as_dict=True)
	)

	custom_fields = (
		frappe.qb.from_(CustomField)
		.select(
			CustomField.fieldname,
			CustomField.fieldtype,
			CustomField.label,
			CustomField.name,
			CustomField.options,
			CustomField.read_only,
			CustomField.idx,
			CustomField.insert_after,
		)
		.where(CustomField.dt == "CRM Lead")
		.where(CustomField.hidden == False)
		.where(Criterion.notin(CustomField.fieldtype, not_allowed_fieldtypes))
		.orderby(CustomField.idx)
		.run(as_dict=True)
	)

	all_fields = []
	all_fields.extend(fields)

	# Add custom fields based on insert_after
	for custom_field in custom_fields:
		if custom_field.insert_after:
			for i, field in enumerate(all_fields):
				if field.fieldname == custom_field.insert_after:
					all_fields.insert(i + 1, custom_field)
					break
		else:
			all_fields.prepend(custom_field)

	sections = {}
	section_fields = []
	last_section = None

	for field in all_fields:
		if field.fieldtype == "Tab Break" and last_section:
			sections[last_section]["fields"] = section_fields
			last_section = None
			if field.read_only:
				section_fields = []
				continue
		if field.fieldtype == "Tab Break":
			section_fields = []
			last_section = field.fieldname
			sections[field.fieldname] = {
				"label": field.label,
				"opened": True,
				"fields": [],
			}
		else:
			section_fields.append(get_field_obj(field))

	lead_fields = []
	for section in sections:
		lead_fields.append(sections[section])

	return lead_fields

def get_field_obj(field):
	obj = {
		"label": field.label,
		"type": get_type(field),
		"name": field.fieldname,
	}

	obj["placeholder"] = "Add " + field.label.lower() + "..."

	if field.fieldtype == "Link":
		obj["placeholder"] = "Select " + field.label.lower() + "..."
		obj["doctype"] = field.options
	elif field.fieldtype == "Select":
		obj["options"] = [{"label": option, "value": option} for option in field.options.split("\n")]

	if field.read_only:
		obj["tooltip"] = "This field is read only and cannot be edited."

	return obj

def get_type(field):
	if field.fieldtype == "Data" and field.options == "Phone":
		return "phone"
	elif field.fieldtype == "Data" and field.options == "Email":
		return "email"
	elif field.read_only:
		return "read_only"
	return field.fieldtype.lower()