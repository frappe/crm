//Lead status translation utilities
//const { __ } = window

// Map of original status values to their translations
export function leadStatusTranslations() {
  return {
    'New': window.__('New'),
    'Contacted': window.__('Contacted'),
    'Nurture': window.__('Nurture'),
    'Qualified': window.__('Qualified'),
    'Unqualified': window.__('Unqualified'),
    'Junk': window.__('Junk')
}
}
// Reverse map for looking up original values from translations
export const reverseLeadStatusTranslations = Object.entries(leadStatusTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a status to localized version
export const translateLeadStatus = (status) => {
  if (!status) return ''
  return window.__(status) // Use __ directly to ensure translation at render time
}

// Get original status from translated version
export function getOriginalLeadStatus(translatedStatus) {
  return reverseLeadStatusTranslations[translatedStatus] || translatedStatus
} 