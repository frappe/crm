import frappe


def execute():
	"""The editor now shows a custom link on its host's row, so a one-host page's own link moves there."""
	frappe.db.sql(
		"""
		UPDATE `tabCRM Booking Page` page
		JOIN `tabCRM Booking Page Host` host
			ON host.parent = page.name AND host.parenttype = 'CRM Booking Page'
		SET host.meeting_link = TRIM(page.location), page.location = ''
		WHERE page.location_type = 'Custom link'
			AND IFNULL(host.meeting_link, '') = ''
			AND TRIM(page.location) REGEXP '^https?://'
			AND (SELECT COUNT(*) FROM `tabCRM Booking Page Host` h
				WHERE h.parent = page.name AND h.parenttype = 'CRM Booking Page') = 1
		"""
	)
