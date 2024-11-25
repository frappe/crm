# import frappe
from frappe.core.doctype.user.user import User

from next_crm.api.demo import validate_reset_password


class CustomUser(User):
    def validate_reset_password(self):
        # restrict demo user to reset password
        validate_reset_password(self)
