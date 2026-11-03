// What CRM Deal's contacts section does, kept free of the desk's imports so it is unit-tested.
import { ref } from 'vue'
import { saveRecord } from '../saveRecord.js'

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

	// The server's validate fetches the row's name, email and mobile and sets the deal's primary ones.
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
		const before = this.page.doc.contacts ?? []
		this.page.doc.contacts = change(before)
		try {
			if (await saveRecord(this.page)) {
				this.page.toast.success(done)
				return true
			}
			// A refused save leaves the draft: only the rows this write changed go back.
			this.page.doc.contacts = before
			return false
		} finally {
			this.busy.value = false
		}
	}
}
