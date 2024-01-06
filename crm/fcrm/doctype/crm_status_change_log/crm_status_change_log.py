# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe.model.document import Document


class CRMStatusChangeLog(Document):
	pass


def add_status_change_log(doc):
	if not doc.is_new():
		last_status_change = doc.status_change_log[-1]
		last_status_change.to = doc.status
		last_status_change.to_date = datetime.now()
		last_status_change.log_owner = frappe.session.user
		last_status_change.duration = (last_status_change.to_date - last_status_change.from_date).total_seconds()

	doc.append("status_change_log", {
		"from": doc.status,
		"to": "",
		"from_date": datetime.now(),
		"to_date": "",
		"log_owner": frappe.session.user,
	})