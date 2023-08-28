import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const contactsStore = defineStore('crm-contacts', () => {
  let contactsByPhone = reactive({})

  const contacts = createResource({
    url: 'crm.api.session.get_contacts',
    cache: 'contacts',
    initialData: [],
    transform(contacts) {
      for (let contact of contacts) {
        contactsByPhone[contact.mobile_no] = contact
      }
      return contacts
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })
  contacts.fetch()

  function getContact(mobile_no) {
    return contactsByPhone[mobile_no]
  }

  return {
    contacts,
    getContact,
  }
})
