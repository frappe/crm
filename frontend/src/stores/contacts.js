import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const contactsStore = defineStore('crm-contacts', () => {
  let contactsByPhone = reactive({})
  let contactsByName = reactive({})

  const contacts = createResource({
    url: 'crm.api.session.get_contacts',
    cache: 'contacts',
    initialData: [],
    auto: true,
    transform(contacts) {
      for (let contact of contacts) {
        contactsByPhone[contact.mobile_no] = contact
        contactsByName[contact.name] = contact
      }
      return contacts
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })

  function getContact(mobile_no) {
    return contactsByPhone[mobile_no]
  }
  function getContactByName(name) {
    return contactsByName[name]
  }

  return {
    contacts,
    getContact,
    getContactByName,
  }
})
