"""Mirror the layouts again after `normalize_layout_field_entries`.

A site that ran the mirror patches before it was normalized mirrored the legacy field dicts as nothing.
"""

from crm.fcrm.doctype.crm_fields_layout.form_layout_mirror import (
	FOREIGN_DOCTYPES,
	MIRRORED_DOCTYPES,
	mirror_all_layouts,
)


def execute():
	mirror_all_layouts(MIRRORED_DOCTYPES + FOREIGN_DOCTYPES)
