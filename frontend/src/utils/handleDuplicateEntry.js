import { call } from 'frappe-ui'

export async function handleDuplicateEntry(error, doctype, retry) {
  if (!error || !error.message) return false

  // Check if this is a duplicate entry error
  if (error.message.includes('DuplicateEntryError')) {
    try {
      // Extract the duplicate ID from the error message
      const match = error.message.match(/'([^']+)'/)
      if (!match) return false

      const duplicateId = match[1]
      
      // Get the series name from the ID (e.g., "CRM-LEAD-2024-" from "CRM-LEAD-2024-00005")
      const seriesMatch = duplicateId.match(/^(.+?)\d+$/)
      if (!seriesMatch) return false

      const seriesName = seriesMatch[1]

      // Get the numeric part of the ID
      const numericPart = parseInt(duplicateId.replace(seriesName, ''))
      if (isNaN(numericPart)) return false

      // Update the series counter
      await call('frappe.client.set_value', {
        doctype: 'Series',
        name: seriesName,
        fieldname: 'current',
        value: numericPart
      })

      // Retry the operation
      if (retry) {
        await retry()
        return true
      }
    } catch (e) {
      console.error('Error handling duplicate entry:', e)
    }
  }
  return false
} 