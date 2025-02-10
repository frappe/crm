/**
 * Normalizes a phone number by removing all non-digit characters except '+' at the start
 * @param {string} phoneNumber - The phone number to normalize
 * @returns {string} - The normalized phone number
 */
export function normalizePhoneNumber(phoneNumber) {
  if (!phoneNumber) return ''
  
  // Remove all non-digit characters
  let normalized = phoneNumber.replace(/\D/g, '')
  
  // Handle Russian numbers
  if (normalized.startsWith('8') || normalized.startsWith('7')) {
    // Remove leading 8 or 7
    normalized = normalized.replace(/^[78]/, '')
    // Add +7 prefix
    normalized = '+7' + normalized
  } else if (!normalized.startsWith('+')) {
    // For other numbers, add + if it doesn't exist
    normalized = '+' + normalized
  }
  
  return normalized
}

/**
 * Formats a phone number for display
 * @param {string} phoneNumber - The normalized phone number
 * @returns {string} - The formatted phone number for display
 */
export function formatPhoneNumber(phoneNumber) {
  const normalized = normalizePhoneNumber(phoneNumber)
  if (!normalized) return ''
  
  // Format Russian numbers like +7 (XXX) XXX-XX-XX
  if (normalized.startsWith('+7') && normalized.length === 12) {
    const groups = normalized.match(/^\+7(\d{3})(\d{3})(\d{2})(\d{2})$/)
    if (groups) {
      return `+7 (${groups[1]}) ${groups[2]}-${groups[3]}-${groups[4]}`
    }
  }
  
  return normalized
}

/**
 * Validates if a phone number is in correct format
 * @param {string} phoneNumber - The phone number to validate
 * @returns {boolean} - Whether the phone number is valid
 */
export function isValidPhoneNumber(phoneNumber) {
  const normalized = normalizePhoneNumber(phoneNumber)
  // For Russian numbers
  if (normalized.startsWith('+7')) {
    return normalized.length === 12
  }
  // For other numbers, basic validation
  return normalized.length >= 10 && /^\+[0-9]+$/.test(normalized)
} 