// What CRM Deal's contacts section does, kept free of the desk's imports so it is unit-tested.
import { ref } from 'vue'
import { saveRecord } from '../saveRecord.js'

const DEAL = 'crm.fcrm.doctype.crm_deal.crm_deal'

export const CONTACT_METHODS = {
	add: `${DEAL}.add_contact`,
	remove: `${DEAL}.remove_contact`,
	setPrimary: `${DEAL}.set_primary_contact`,
}

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

/** The add, remove and set-primary writes, one at a time; each resolves true once it is done. */
export class ContactsEditor {
	constructor(page, messages) {
		this.page = page
		this.messages = messages
		this.busy = ref(false)
	}

	get editable() {
		return Boolean(this.page.perms?.write) && this.page.fieldAccess('contacts') === 'write'
	}

	add(contact) {
		if (dealContacts(this.page.doc).some((row) => row.contact === contact)) {
			this.page.toast.error(this.messages.duplicate)
			return Promise.resolve(false)
		}
		return this.#change(CONTACT_METHODS.add, contact, this.messages.added)
	}

	remove(contact) {
		return this.#change(CONTACT_METHODS.remove, contact, this.messages.removed)
	}

	setPrimary(contact) {
		return this.#change(CONTACT_METHODS.setPrimary, contact, this.messages.primary)
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

	async #change(method, contact, done) {
		if (this.busy.value) return false
		this.busy.value = true
		try {
			return await this.#write(method, contact, done)
		} finally {
			this.busy.value = false
		}
	}

	async #write(method, contact, done) {
		// The server saves the deal: a draft goes first, and the re-read keeps the next save from conflicting.
		if (!(await saveRecord(this.page))) return false
		try {
			await this.page.call(method, { deal: this.page.docname, contact })
		} catch (error) {
			this.page.toast.error(error?.message || String(error))
			return false
		}
		// A re-read would drop edits typed during the call; the next save's conflict dialog keeps them.
		if (!this.page.isDirty) await this.page.reload()
		this.page.toast.success(done)
		return true
	}
}
