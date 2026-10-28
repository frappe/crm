// Which CRM Telephony Agent rows the Profile pane's Telephony block draws, in order.

const SHOWN_WHEN = {
	mobile_no: () => true,
	default_medium: (on) => Boolean(on.twilio || on.exotel),
	call_receiving_device: () => true,
	twilio_number: (on) => Boolean(on.twilio),
	exotel_number: (on) => Boolean(on.exotel),
}

/** The fieldnames to draw while `providers` (`{ twilio, exotel }`) are on. */
export function telephonyRows(providers) {
	return Object.keys(SHOWN_WHEN).filter((fieldname) => SHOWN_WHEN[fieldname](providers))
}
