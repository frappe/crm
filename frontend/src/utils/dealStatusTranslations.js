// Deal status translation utilities
//const { __ } = window

// Map of original status values to their translations
export const dealStatusTranslations = {
  'Qualification': __('Qualification'),
  'Demo/Making': __('Demo/Making'),
  'Proposal/Quotation': __('Proposal/Quotation'),
  'Negotiation': __('Negotiation'),
  'Ready to Close': __('Ready to Close'),
  'Won': __('Won'),
  'Lost': __('Lost'),
}

// Reverse map for looking up original values from translations
export const reverseDealStatusTranslations = Object.entries(dealStatusTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a status to localized version
export function translateDealStatus(status) {
  if (!status) return ''
  return __(status) // Use __ directly to ensure translation at render time
}

// Get original status from translated version
export function getOriginalDealStatus(translatedStatus) {
  return reverseDealStatusTranslations[translatedStatus] || translatedStatus
} 