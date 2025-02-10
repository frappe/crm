// Smart filter utility to detect and parse different types of input

/**
 * Detects the type of input and returns appropriate filter parameters
 * @param {string} input - The search input
 * @param {string} doctype - The document type
 * @returns {Object} Filter parameters object
 */
export function parseSmartFilter(input, doctype) {
  if (!input) return null;

  // Normalize input
  const normalizedInput = input.trim();

  // Common patterns
  const phonePattern = /^\d+$/;
  const websitePattern = /^[^\s]+\.[^\s]+$/;
  const emailPattern = /^[^\s@]+@|@[^\s@]+$/;  // Matches either something@... or ...@something

  // Handle different doctypes
  switch (doctype) {
    case 'CRM Organization':
      if (websitePattern.test(normalizedInput)) {
        return {
          website: ['LIKE', `%${normalizedInput}%`]
        };
      }
      return {
        industry: ['LIKE', `%${normalizedInput}%`]
      };

    case 'CRM Deal':
      if (phonePattern.test(normalizedInput)) {
        return {
          mobile_no: ['LIKE', `%${normalizedInput}%`]
        };
      }
      if (normalizedInput.includes('@')) {
        return {
          email: ['LIKE', `%${normalizedInput}%`]
        };
      }
      return {
        organization: ['LIKE', `%${normalizedInput}%`]
      };

    case 'Contact':
      if (phonePattern.test(normalizedInput)) {
        return {
          mobile_no: ['LIKE', `%${normalizedInput}%`]
        };
      }
      if (emailPattern.test(normalizedInput)) {
        return {
          email_id: ['LIKE', `%${normalizedInput}%`]
        };
      }
      return {
        company_name: ['LIKE', `%${normalizedInput}%`]
      };

    case 'CRM Lead':
    default:
      if (phonePattern.test(normalizedInput)) {
        return {
          mobile_no: ['LIKE', `%${normalizedInput}%`]
        };
      }
      if (normalizedInput.includes('@')) {
        return {
          email: ['LIKE', `%${normalizedInput}%`]
        };
      }
      return {
        lead_name: ['LIKE', `%${normalizedInput}%`]
      };
  }
}

/**
 * Converts smart filter parameters to the format expected by the filtering system
 * @param {Object} smartFilterParams - Parameters from parseSmartFilter
 * @returns {Object} Formatted filter parameters
 */
export function formatSmartFilterParams(smartFilterParams) {
  if (!smartFilterParams) return {};
  return smartFilterParams;
} 