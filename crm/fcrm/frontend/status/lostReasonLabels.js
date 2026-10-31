// Out of statusChange.js on purpose: `frappe/i18n` there would break its vitest import.
import { __ } from 'frappe/i18n'

export function lostReasonLabels() {
	return { title: __('Lost Reason'), submitLabel: __('Save'), cancelLabel: __('Cancel') }
}
