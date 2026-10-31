from crm.fcrm.doctype.crm_fields_layout.form_layout_mirror import FOREIGN_DOCTYPES, mirror_all_layouts


def execute():
	mirror_all_layouts(FOREIGN_DOCTYPES)
