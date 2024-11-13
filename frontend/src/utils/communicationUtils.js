import { createResource, getCachedDocumentResource } from 'frappe-ui'
import { errorMessage } from '@/utils'
import { capture } from '@/telemetry'
import { usersStore } from '@/stores/users'
const { getUser } = usersStore()

function normalizePhoneNumber(phoneNumber) {
  // Remove all non-digit characters
  let normalizedNumber = phoneNumber.replace(/\D/g, '')
  
  // If number starts with 8, replace it with 7
  if (normalizedNumber.startsWith('8')) {
    normalizedNumber = '7' + normalizedNumber.slice(1)
  }
  
  // Add plus sign if not present
  return normalizedNumber.startsWith('+') ? normalizedNumber : `+${normalizedNumber}`
}

export function trackCommunication({ type, doctype, docname, phoneNumber, activities, contactName }) {
  if (!phoneNumber) return errorMessage(__('No phone number set'))

  const formattedNumber = normalizePhoneNumber(phoneNumber)

  //console.log('Starting communication tracking:', {
  //  type,
  //  doctype,
  //  docname,
  //  phoneNumber: formattedNumber
  //})

  // First trigger the action
  if (type === 'phone') {
    //console.log('Initiating phone call to:', formattedNumber)
    window.location.href = `tel:${formattedNumber}`
  } else {
    //console.log('Opening WhatsApp for:', formattedNumber)
    window.open(`https://wa.me/${formattedNumber}`, '_blank')
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
      phone_no: formattedNumber,
      content: type === 'phone' 
<<<<<<< HEAD
        ? __('Call initiated to {0}', [formattedNumber])
        : __('Chat initiated with {0}', [formattedNumber]),
=======
        ? __(`Call initiated to {0}`,[phoneNumber])
        : __(`Chat initiated with {0}`,[phoneNumber]),
>>>>>>> 932b28c (Updating translations)
      subject: type === 'phone' 
        ? __('Phone call')
        : __('WhatsApp chat'),
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

export { normalizePhoneNumber }

