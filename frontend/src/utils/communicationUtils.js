import { createResource, getCachedDocumentResource } from 'frappe-ui'
import { errorMessage } from '@/utils'
import { capture } from '@/telemetry'
import { usersStore } from '@/stores/users'
const { getUser } = usersStore()

export function trackCommunication({ type, doctype, docname, phoneNumber, activities, contactName }) {
  if (!phoneNumber) return errorMessage(__('No phone number set'))

  console.log('Starting communication tracking:', {
    type,
    doctype,
    docname,
    phoneNumber
  })

  // First trigger the action
  if (type === 'phone') {
    //console.log('Initiating phone call to:', phoneNumber)
    window.location.href = `tel:${phoneNumber}`
  } else {
    //console.log('Opening WhatsApp for:', phoneNumber)
    window.open(`https://wa.me/${phoneNumber}`, '_blank')
  }

  const params = {
    doc: {
      doctype: 'Communication',
      communication_type: 'Communication',
      communication_medium: type === 'phone' ? 'Phone' : 'Chat',
      sent_or_received: 'Sent',
      recipients: contactName,
      status: 'Linked',
      reference_doctype: doctype,
      reference_name: docname,
      phone_no: phoneNumber,
      content: type === 'phone' 
        ? __(`Call initiated to ${phoneNumber}`)
        : __(`Chat initiated with ${phoneNumber}`),
      subject: type === 'phone' 
        ? __(`Phone call`)
        : __(`WhatsApp chat`),
      sender: getUser()?.full_name || undefined
    }
  }

  //console.log('Attempting to log communication with params:', params)

  // Log communication using CRM's API
  const logCommunication = createResource({
    url: 'frappe.client.insert',
    params: params,
    onSuccess: (response) => {
      //console.log('Communication successfully logged:', response)
      console.log('Reloading activities:', activities)
      activities?.all_activities?.reload()
      capture(type === 'phone' ? 'phone_call_initiated' : 'whatsapp_chat_initiated')
    },
    onError: (error) => {
      console.error('Communication log error:', error)
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        params: params
      })
      if (error.xhr) {
        console.error('Server response:', {
          status: error.xhr.status,
          response: error.xhr.response,
          responseText: error.xhr.responseText
        })
      }
      errorMessage(error.message)
    }
  })

  //console.log('Submitting communication log request...')
  
  try {
    logCommunication.submit()
    //console.log('Request submitted successfully')
  } catch (e) {
    //console.error('Error submitting request:', e)
  }
}

