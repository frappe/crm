// The contacts section on CRM Deal's side panel, above the Side Panel layout's sections.
import { __ } from 'frappe/i18n'
import DealContacts from './DealContacts.vue'
import DealContactsAdd from './DealContactsAdd.vue'
import { ContactsEditor, placeContactsSection } from './dealContacts.js'

export function addContactsSection(page) {
	// One editor for the header's picker and the rows, so they share one write at a time.
	const editor = new ContactsEditor(page, {
		duplicate: __('Contact already added'),
		added: __('Contact added'),
		removed: __('Contact removed'),
		primary: __('Primary contact set'),
	})
	// The panel translates the label against the doctype.
	placeContactsSection(page, {
		label: 'Contacts',
		component: DealContacts,
		actions: DealContactsAdd,
		props: { editor },
	})
}
