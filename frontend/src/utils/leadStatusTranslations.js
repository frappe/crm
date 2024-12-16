// Lead status translation utilities
const { __ } = window

// Map of original status values to their translations
export const leadStatusTranslations = {
  'New': __('New'),
  'Contacted': __('Contacted'),
  'Nurture': __('Nurture'),
  'Qualified': __('Qualified'),
  'Unqualified': __('Unqualified'),
  'Junk': __('Junk')
}

// Reverse map for looking up original values from translations
export const reverseLeadStatusTranslations = Object.entries(leadStatusTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a status to localized version
export function translateLeadStatus(status) {
  if (!status) return ''
  return __(status) // Use __ directly to ensure translation at render time
}

// Get original status from translated version
export function getOriginalLeadStatus(translatedStatus) {
  return reverseLeadStatusTranslations[translatedStatus] || translatedStatus
} 