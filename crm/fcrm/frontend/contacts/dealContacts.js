// What CRM Deal's contacts section does, kept free of the desk's imports so it is unit-tested.
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
	page.panelSections.add({ name: 'contacts', ...section }, { before: FIRST_LAYOUT_SECTION })
}

/** The deal's contact rows, the primary one first, the rest in table order. */
export function dealContacts(doc) {
	const rows = (doc?.contacts ?? []).filter((row) => row.contact)
	return rows.sort((a, b) => Number(Boolean(b.is_primary)) - Number(Boolean(a.is_primary)))
}

/** The add, remove and set-primary writes; each resolves true once the page shows the result. */
export class ContactsEditor {
	constructor(page, messages) {
		this.page = page
		this.messages = messages
	}

	get editable() {
		return Boolean(this.page.perms?.write)
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

	async #change(method, contact, done) {
		// The server saves the deal: a draft goes first, and the re-read keeps the next save from conflicting.
		if (!(await saveRecord(this.page))) return false
		try {
			await this.page.call(method, { deal: this.page.docname, contact })
		} catch (error) {
			this.page.toast.error(error?.message || String(error))
			return false
		}
		await this.page.reload()
		this.page.toast.success(done)
		return true
	}
}
