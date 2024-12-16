// Task status translation utilities
const { __ } = window

// Map of original status values to their translations
export const taskStatusTranslations = {
  'Backlog': __('Backlog'),
  'Todo': __('Todo'),
  'In Progress': __('In Progress'),
  'Done': __('Done'),
  'Canceled': __('Canceled')
}

// Reverse map for looking up original values from translations
export const reverseTaskStatusTranslations = Object.entries(taskStatusTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a status to localized version
export function translateTaskStatus(status) {
  if (!status) return ''
  return __(status) // Use __ directly to ensure translation at render time
}

// Get original status from translated version
export function getOriginalTaskStatus(translatedStatus) {
  return reverseTaskStatusTranslations[translatedStatus] || translatedStatus
} 