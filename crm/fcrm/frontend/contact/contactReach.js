// What Contact's email and mobile pickers do on `/apps/crm`, kept free of the desk's imports so it is unit-tested.
import { ServerWrites } from '../serverWrites.js'

export const REACH_METHODS = {
	setPrimary: 'crm.api.contact.set_as_primary',
	add: 'crm.api.contact.create_new',
}

// The two methods spell the mobile differently: `mobile_no` to set the primary, `phone` to add one.
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

// The panel unmounts the picker on every close: one editor per page keeps its stale lock across reopens.
const editors = new WeakMap()

/** The page's editor for one picker, made on first use. */
export function reachEditor(page, fieldname, messages) {
	if (!editors.has(page)) editors.set(page, {})
	const byField = editors.get(page)
	byField[fieldname] ??= new ReachEditor(page, fieldname, messages)
	return byField[fieldname]
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

	/** The contact's values in table order, each once; a primary no row holds still shows, first. */
	values() {
		const rows = this.page.doc?.[this.reach.table] ?? []
		const current = this.page.doc?.[this.fieldname]
		const values = [...new Set(rows.map((row) => row[this.reach.column]).filter(Boolean))]
		return current && !values.includes(current) ? [current, ...values] : values
	}

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
