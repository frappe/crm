import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive } from 'vue'

export const contactsStore = defineStore('crm-contacts', () => {
  let contactsByPhone = reactive({})
  let contactsByName = reactive({})
  let leadContactsByPhone = reactive({})
  let allContacts = reactive([])

  const contacts = createResource({
    url: 'crm.api.session.get_contacts',
    cache: 'contacts',
    initialData: [],
    auto: true,
    transform(contacts) {
      for (let contact of contacts) {
        // remove special characters from phone number to make it easier to search
        // also remove spaces but keep + sign at the start
        contact.actual_mobile_no = contact.mobile_no
        contact.mobile_no = contact.mobile_no?.replace(/[^0-9+]/g, '')
        contactsByPhone[contact.mobile_no] = contact
        contactsByName[contact.name] = contact
      }
      allContacts = [...contacts]
      return contacts
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })

  const leadContacts = createResource({
    url: 'crm.api.session.get_lead_contacts',
    cache: 'lead_contacts',
    initialData: [],
    auto: true,
    transform(lead_contacts) {
      for (let lead_contact of lead_contacts) {
        // remove special characters from phone number to make it easier to search
        // also remove spaces but keep + sign at the start
        lead_contact.mobile_no = lead_contact.mobile_no?.replace(/[^0-9+]/g, '')
        lead_contact.full_name = lead_contact.lead_name
        leadContactsByPhone[lead_contact.mobile_no] = lead_contact
      }
      return lead_contacts
    },
    onError(error) {
      if (error && error.exc_type === 'AuthenticationError') {
        router.push('/login')
      }
    },
  })

  function getContact(mobile_no) {
    mobile_no = mobile_no?.replace(/[^0-9+]/g, '')
    return contactsByPhone[mobile_no]
  }
  function getContactByName(name) {
    return contactsByName[name]
  }
  function getLeadContact(mobile_no) {
    mobile_no = mobile_no?.replace(/[^0-9+]/g, '')
    return leadContactsByPhone[mobile_no]
  }

  function getContacts() {
    return allContacts || contacts?.data || []
  }

  return {
    contacts,
    getContacts,
    getContact,
    getContactByName,
    getLeadContact,
  }
})
