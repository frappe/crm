// Task status translation utilities
//const { __ } = window

// Map of original status values to their translations
export function taskStatusTranslations() {
  return {
    'Backlog': window.__('Backlog'),
    'Todo': window.__('Todo'),
    'In Progress': window.__('In Progress'),
    'Done': window.__('Done'),
    'Canceled': window.__('Canceled')
  }
}

// Reverse map for looking up original values from translations
export const reverseTaskStatusTranslations = Object.entries(taskStatusTranslations)
  .reduce((acc, [key, value]) => {
    acc[value] = key
    return acc
  }, {})

// Translate a status to localized version
export const translateTaskStatus = (status) => {
  if (!status) return ''
  return window.__(status) // Use __ directly to ensure translation at render time
}

// Get original status from translated version
export function getOriginalTaskStatus(translatedStatus) {
  return reverseTaskStatusTranslations[translatedStatus] || translatedStatus
} 