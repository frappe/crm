# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HelpdeskCRMSettings(Document):
	def validate(self):
		if self.enabled:
			self.validate_if_helpdesk_installed()
			self.create_helpdesk_script()

	def validate_if_helpdesk_installed(self):
		if not self.is_helpdesk_in_different_site:
			if "helpdesk" not in frappe.get_installed_apps():
				frappe.throw(_("Helpdesk is not installed in the current site"))

	def create_helpdesk_script(self):
		if not frappe.db.exists("CRM Form Script", "Helpdesk Integration Script"):
			script = get_helpdesk_script()
			frappe.get_doc(
				{
					"doctype": "CRM Form Script",
					"name": "Helpdesk Integration Script",
					"dt": "CRM Deal",
					"view": "Form",
					"script": script,
					"enabled": 1,
					"is_standard": 1,
				}
			).insert()


@frappe.whitelist()
def create_customer_in_helpdesk(name, email):
	helpdesk_crm_settings = frappe.get_single("Helpdesk CRM Settings")
	if not helpdesk_crm_settings.enabled:
		frappe.throw(_("Helpdesk is not integrated with the CRM"))

	if not helpdesk_crm_settings.is_helpdesk_in_different_site:
		# from helpdesk.integrations.crm.api import create_customer
		return create_customer(name, email)


def get_helpdesk_script():
	return """class CRMDeal {
    onLoad() {
        this.actions.push(
            {
                group: "Helpdesk",
                hideLabel: true,
                items: [
                    {
                        label: "Create customer in Helpdesk",
                        onClick: () => {
                            call('crm.fcrm.doctype.helpdesk_crm_settings.helpdesk_crm_settings.create_customer_in_helpdesk', {
                                name: this.doc.organization,
                                email: this.doc.email
                            }).then((a) => {
                                toast.success("Customer created successfully, " + a.customer)
                            })
                        }
                    }
                ]
            }
        )
    }
}"""


# Helpdesk methods TODO: move to helpdesk.integrations.crm.api
def create_customer(name, email):
	customer = frappe.db.exists("HD Customer", name)
	if not customer:
		customer = frappe.get_doc(
			{
				"doctype": "HD Customer",
				"customer_name": name,
			}
		)
		customer.insert(ignore_permissions=True, ignore_if_duplicate=True)
	else:
		customer = frappe.get_doc("HD Customer", customer)

	contact = frappe.db.exists("Contact", {"email_id": email})
	if contact:
		contact = frappe.get_doc("Contact", contact)
		contact.append("links", {"link_doctype": "HD Customer", "link_name": customer.name})
		contact.save(ignore_permissions=True)
	else:
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": email.split("@")[0],
				"email_ids": [{"email_id": email, "is_primary": 1}],
				"links": [{"link_doctype": "HD Customer", "link_name": customer.name}],
			}
		)
		contact.insert(ignore_permissions=True)

	if not frappe.db.exists("User", contact.email_id):
		invite_user(contact.name)
	else:
		base_url = frappe.utils.get_url() + "/helpdesk"
		frappe.sendmail(
			recipients=[contact.email_id],
			subject="Welcome existing user to Helpdesk",
			message=f"""
				<h1>Hello,</h1>
				<button>{base_url}</button>
			""",
			now=True,
		)

	return {"customer": customer.name, "contact": contact.name}


def invite_user(contact: str):
	contact = frappe.get_doc("Contact", contact)
	contact.check_permission()

	if not contact.email_id:
		frappe.throw(_("Please set Email Address"))

	user = frappe.get_doc(
		{
			"doctype": "User",
			"first_name": contact.first_name,
			"last_name": contact.last_name,
			"email": contact.email_id,
			"user_type": "Website User",
			"send_welcome_email": 0,
		}
	).insert()

	contact.user = user.name
	contact.save(ignore_permissions=True)

	send_welcome_mail_to_user(user)
	return user.name


def send_welcome_mail_to_user(user):
	from frappe.utils import get_url
	from frappe.utils.user import get_user_fullname

	link = user.reset_password()

	frappe.cache.hset("redirect_after_login", user.name, "/helpdesk")

	site_url = get_url()
	subject = _("Welcome to Helpdesk")

	created_by = get_user_fullname(frappe.session["user"])
	if created_by == "Guest":
		created_by = "Administrator"

	args = {
		"first_name": user.first_name or user.last_name or "user",
		"last_name": user.last_name,
		"user": user.name,
		"title": subject,
		"login_url": get_url(),
		"created_by": created_by,
		"site_url": site_url,
		"link": link,
	}

	frappe.sendmail(
		recipients=[user.email],
		subject=subject,
		template="helpdesk_invitation",
		args=args,
		now=True,
	)
