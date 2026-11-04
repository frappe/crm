// The Task, Note and Call Log rows on the Activity tab of CRM Deal and CRM Lead.
import RecordActivityRow from './RecordActivityRow.vue'
import { activityItem, fetchActivityRows, referenceNames } from './activityRows.js'

export function addActivityRows(page) {
	if (page.isNew) return
	const names = referenceNames(page)
	// The deal's lead is part of the key: converting a lead changes which records the deal lists.
	const rows = page.cached(`activity-rows:${names.join('|')}`, fetchActivityRows(page, names))
	for (const row of rows ?? []) page.activity.add(activityItem(row, RecordActivityRow))
}
