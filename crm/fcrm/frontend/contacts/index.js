// The contacts section on CRM Deal's side panel, above the Side Panel layout's sections.
import DealContacts from './DealContacts.vue'
import { placeContactsSection } from './dealContacts.js'

export function addContactsSection(page) {
	// The panel translates the label against the doctype.
	placeContactsSection(page, { label: 'Contacts', component: DealContacts })
}
