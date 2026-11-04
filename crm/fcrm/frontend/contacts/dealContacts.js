// What CRM Deal's contacts section does, kept free of the desk's imports so it is unit-tested.
import { ref, toRaw } from 'vue'
import { saveRecord } from '../saveRecord.js'
import { callState } from '../telephony/callState.js'
import { MAKE_A_CALL } from '../telephony/makeCall.js'

// The layout move puts the SLA section first in every Deal Side Panel (#45882 Q6).
export const FIRST_LAYOUT_SECTION = 'sla_section'

/** Adds the section above the Side Panel layout's own sections; a new deal has no contacts to edit. */
export function placeContactsSection(page, section) {
	if (page.isNew) return
	const position = page.panelSections.has(FIRST_LAYOUT_SECTION)
		? { before: FIRST_LAYOUT_SECTION }
		: { after: 'people' }
	page.panelSections.add({ name: 'contacts', ...section }, position)
}

/** The deal's contact rows, the primary one first, the rest in table order. */
export function dealContacts(doc) {
	const rows = (doc?.contacts ?? []).filter((row) => row.contact)
	return rows.sort((a, b) => Number(Boolean(b.is_primary)) - Number(Boolean(a.is_primary)))
}

/** Whether a mobile number dials; reactive, since the user's media land after the first paint. */
export function canCall() {
	return callState.media.length > 0
}

/** Dials through the call window, as "Make a call" does; a refused act is told in a toast. */
export async function callContact(page, number) {
	try {
		await page.run(MAKE_A_CALL, number)
	} catch (error) {
		page.toast.error(error?.message || String(error))
	}
}

/** Whether the deal offers its email writer: not without the email right, nor once a script hides it. */
export function canEmail(page) {
	return page.composer.has('email')
}

/** Opens the deal's email writer to the contact; an email draft already in memory keeps its To. */
export function emailContact(page, email) {
	page.composer.open('email', { draft: { to: [email] } })
}

/** Edits the draft's contacts table and saves it, one write at a time; each resolves true once saved. */
export class ContactsEditor {
	constructor(page, messages) {
		this.page = page
		this.messages = messages
		this.busy = ref(false)
	}

	get editable() {
		return Boolean(this.page.perms?.write) && this.page.fieldAccess('contacts') === 'write'
	}

	// The server fills the row's name, email and mobile from the Contact on save.
	add(contact) {
		if (dealContacts(this.page.doc).some((row) => row.contact === contact)) {
			this.page.toast.error(this.messages.duplicate)
			return Promise.resolve(false)
		}
		return this.#write((rows) => [...rows, { contact }], this.messages.added)
	}

	remove(contact) {
		return this.#write(
			(rows) => rows.filter((row) => row.contact !== contact),
			this.messages.removed
		)
	}

	setPrimary(contact) {
		const mark = (row) => ({
			...row,
			is_primary: row.contact === contact ? 1 : 0,
		})
		return this.#write((rows) => rows.map(mark), this.messages.primary)
	}

	/** Creates a contact in its Quick Entry, then adds it; false when nothing was saved. */
	async create(values) {
		let contact
		try {
			contact = await this.page.create('Contact', { values })
		} catch (error) {
			this.page.toast.error(error?.message || String(error))
			return false
		}
		return contact ? this.add(contact.name) : false
	}

	async #write(change, done) {
		if (this.busy.value) return false
		this.busy.value = true
		try {
			// A running save would take this change in and then drop it for the server's copy.
			if (this.page.isDirty && !(await saveRecord(this.page))) return false
			return await this.#save(change, done)
		} finally {
			this.busy.value = false
		}
	}

	async #save(change, done) {
		const before = this.page.doc.contacts ?? []
		const after = change(before)
		this.page.doc.contacts = after
		if (await saveRecord(this.page)) {
			this.page.toast.success(done)
			return true
		}
		// A conflict's reload replaces the draft: put the rows back only on the draft this write changed.
		if (toRaw(this.page.doc.contacts) === toRaw(after)) this.page.doc.contacts = before
		return false
	}
}
