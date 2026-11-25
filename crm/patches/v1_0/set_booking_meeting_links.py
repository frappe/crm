import frappe


def execute():
	"""Bookings made before CRM Booking had a meeting link kept it only as their Event's
	location. Copy it over for pages with a custom link, the only type that put one there."""
	frappe.db.sql(
		"""
		UPDATE `tabCRM Booking` booking
		JOIN `tabCRM Booking Page` page ON page.name = booking.booking_page
		JOIN `tabEvent` event ON event.name = booking.event
		SET booking.meeting_link = TRIM(event.location)
		WHERE page.location_type = 'Custom link'
			AND IFNULL(booking.meeting_link, '') = ''
			AND TRIM(event.location) REGEXP '^https?://'
		"""
	)
