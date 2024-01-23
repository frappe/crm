# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe.utils import add_to_date
from frappe.model.document import Document


class CRMStatusChangeLog(Document):
	pass


def add_status_change_log(doc):
	if not doc.is_new():
		previous_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
		if not doc.status_change_log and previous_status:
			now_minus_one_minute = add_to_date(datetime.now(), minutes=-1)
			doc.append("status_change_log", {
				"from": previous_status,
				"to": "",
				"from_date": now_minus_one_minute,
				"to_date": "",
				"log_owner": frappe.session.user,
			})
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