import { useFieldDisplay } from '@framework/ui/FormLayout'
import { findStatus, statusInk } from '../status/statusChange.js'

const DEAL_VALUE = { fieldname: 'deal_value', fieldtype: 'Currency', options: 'currency' }

/** `statuses` is a getter for the tab's deal statuses, read on each call. */
export function useDealCells(statuses) {
	const display = useFieldDisplay()
	return {
		ink: (status) => statusInk(findStatus(statuses(), status)?.color),
		amount: (row) => display(DEAL_VALUE, row.deal_value, { doc: row }),
	}
}
