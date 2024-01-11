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
        // remove special characters from phone number to make it easier to search
        // also remove spaces but keep + sign at the start
        contact.mobile_no = contact.mobile_no.replace(/[^0-9+]/g, '')
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
    mobile_no = mobile_no.replace(/[^0-9+]/g, '')
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
