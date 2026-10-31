// The save before an act the server runs on the saved record, kept free of the desk's imports so it is unit-tested.
import { SHOWN_IN_DIALOG } from './status/statusChange.js'

/** Saves the page's edits; false, with the reason shown, when refused. Thrown, a refusal would reload over the draft. */
export async function saveRecord(page) {
	try {
		await page.save()
		return true
	} catch (error) {
		if (!SHOWN_IN_DIALOG.includes(error?.name)) page.toast.error(error?.message || String(error))
		return false
	}
}
