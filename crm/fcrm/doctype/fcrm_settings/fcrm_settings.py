# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from crm.install import after_install


class FCRMSettings(Document):
	@frappe.whitelist()
	def restore_defaults(self, force=False):
		after_install(force)


@frappe.whitelist()
def get_fcrm_settings():
    try:
        fcrm_settings = frappe.get_doc('FCRM Settings')
        return fcrm_settings.as_dict()
    except frappe.DoesNotExistError:
        frappe.throw(_('FCRM Settings document does not exist.'))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Error in get_fcrm_settings')
        frappe.throw(_('An unexpected error occurred: {0}').format(str(e)))
