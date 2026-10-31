// What Contact's email and mobile pickers do on `/apps/crm`, kept free of the desk's imports so it is unit-tested.
import { ServerWrites } from '../serverWrites.js'

export const REACH_METHODS = {
	setPrimary: 'crm.api.contact.set_as_primary',
	add: 'crm.api.contact.create_new',
}

// Per picker: the child table it reads, that table's value column, and the `field` each method expects.
export const REACH = {
	email_id: { table: 'email_ids', column: 'email_id', primaryAs: 'email', addAs: 'email' },
	mobile_no: { table: 'phone_nos', column: 'phone', primaryAs: 'mobile_no', addAs: 'phone' },
}

/** Swaps the read-only email and mobile for pickers on `/apps/crm`; `/apps/desk` and a new contact keep frappe's fields. */
export function placeReachPickers(page, component) {
	if (page.app !== 'crm' || page.isNew || !page.perms?.write) return
	for (const [fieldname, { table }] of Object.entries(REACH)) {
		if (page.fieldAccess(table) !== 'write') continue
		// Writable, or the panel draws the value and never opens the picker.
		page.fields.update(fieldname, { read_only: false, component, props: { page } })
	}
}

/** One picker's choices and writes: the primary comes from the contact's rows, a new value is added to them. */
export class ReachEditor {
	constructor(page, fieldname, messages) {
		this.page = page
		this.fieldname = fieldname
		this.reach = REACH[fieldname]
		this.messages = messages
		this.writes = new ServerWrites(page, messages.stale)
		this.busy = this.writes.busy
	}

	/** The contact's values for this picker, in table order, each once. */
	values() {
		const rows = this.page.doc?.[this.reach.table] ?? []
		return [...new Set(rows.map((row) => row[this.reach.column]).filter(Boolean))]
	}

	/** Whether the typed value is new to the contact. */
	canAdd(value) {
		const typed = value?.trim()
		return Boolean(typed) && !this.values().includes(typed)
	}

	setPrimary(value) {
		if (!value || value === this.page.doc?.[this.fieldname]) return Promise.resolve(false)
		return this.#write(REACH_METHODS.setPrimary, this.reach.primaryAs, value, this.messages.primary)
	}

	add(value) {
		if (!this.canAdd(value)) return Promise.resolve(false)
		return this.#write(REACH_METHODS.add, this.reach.addAs, value.trim(), this.messages.added)
	}

	#write(method, field, value, done) {
		return this.writes.run(method, { contact: this.page.docname, field, value }, done)
	}
}
