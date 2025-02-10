// Task priority translation utilities
//const { __ } = window

// Map of original priority values to their translations
export function taskPriorityTranslations() {
  return {
    'Low': window.__('Low'),
    'Medium': window.__('Medium'),
    'High': window.__('High')
  }
}

// Reverse map for looking up original values from translations
export const reverseTaskPriorityTranslations = Object.entries(taskPriorityTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a priority to localized version
export const translateTaskPriority = (priority) => {
  if (!priority) return ''
  return window.__(priority) // Use __ directly to ensure translation at render time
}

// Get original priority from translated version
export function getOriginalTaskPriority(translatedPriority) {
  return reverseTaskPriorityTranslations[translatedPriority] || translatedPriority
} 