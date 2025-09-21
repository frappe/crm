# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime


class CRMStatusChangeLog(Document):
	pass


def get_duration(from_date, to_date):
	if not isinstance(from_date, datetime):
		from_date = get_datetime(from_date)
	if not isinstance(to_date, datetime):
		to_date = get_datetime(to_date)
	duration = to_date - from_date
	return duration.total_seconds()


def add_status_change_log(doc):
	to_status_type = frappe.db.get_value("CRM Deal Status", doc.status, "type") if doc.status else None

	if not doc.is_new():
		previous_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
		previous_status_type = (
			frappe.db.get_value("CRM Deal Status", previous_status, "type") if previous_status else None
		)
		if not doc.status_change_log and previous_status:
			now_minus_one_minute = add_to_date(datetime.now(), minutes=-1)
			doc.append(
				"status_change_log",
				{
					"from": previous_status,
					"from_type": previous_status_type or "",
					"to": "",
					"to_type": "",
					"from_date": now_minus_one_minute,
					"to_date": "",
					"log_owner": frappe.session.user,
				},
			)
		last_status_change = doc.status_change_log[-1]
		last_status_change.to = doc.status
		last_status_change.to_type = to_status_type or ""
		last_status_change.to_date = datetime.now()
		last_status_change.log_owner = frappe.session.user
		last_status_change.duration = get_duration(last_status_change.from_date, last_status_change.to_date)

	doc.append(
		"status_change_log",
		{
			"from": doc.status,
			"from_type": to_status_type or "",
			"to": "",
			"to_type": "",
			"from_date": datetime.now(),
			"to_date": "",
			"log_owner": frappe.session.user,
		},
	)
