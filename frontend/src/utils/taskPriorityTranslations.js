// Task priority translation utilities
const { __ } = window

// Map of original priority values to their translations
export const taskPriorityTranslations = {
  'Low': __('Low'),
  'Medium': __('Medium'),
  'High': __('High')
}

// Reverse map for looking up original values from translations
export const reverseTaskPriorityTranslations = Object.entries(taskPriorityTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a priority to localized version
export function translateTaskPriority(priority) {
  if (!priority) return ''
  return __(priority) // Use __ directly to ensure translation at render time
}

// Get original priority from translated version
export function getOriginalTaskPriority(translatedPriority) {
  return reverseTaskPriorityTranslations[translatedPriority] || translatedPriority
} 