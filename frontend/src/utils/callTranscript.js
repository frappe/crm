/**
 * Pure utility functions for call transcription handling and formatting.
 */

/**
 * Format an array of speech utterances into the standard CRM transcript string.
 * @param {Array<{ speaker: string, text: string }>} utterances
 * @returns {string} Formatted transcript
 */
export function formatTranscriptUtterances(utterances) {
  if (!Array.isArray(utterances) || utterances.length === 0) {
    return ''
  }

  return utterances
    .filter((u) => u && typeof u.text === 'string' && u.text.trim().length > 0)
    .map((u) => {
      const speakerLabel =
        (u.speaker || '').toLowerCase() === 'agent' ? 'Agent' : 'Customer'
      return `[${speakerLabel}]\n${u.text.trim()}`
    })
    .join('\n\n')
}

/**
 * Determine and normalize the speaker name from Twilio track data.
 * @param {string} [label] - Explicit track label (e.g., 'customer' or 'agent')
 * @param {string} [track] - 'inbound_track' or 'outbound_track'
 * @param {string} [callType] - 'Outgoing' or 'Incoming'
 * @returns {'customer' | 'agent'}
 */
export function normalizeTranscriptSpeaker(
  label = '',
  track = '',
  callType = 'Outgoing',
) {
  const normLabel = (label || '').toLowerCase().trim()
  if (['customer', 'caller', 'client', 'lead'].includes(normLabel)) {
    return 'customer'
  }
  if (['agent', 'user', 'salesperson', 'callee'].includes(normLabel)) {
    return 'agent'
  }

  // Fallback to track + callType direction
  if (track === 'inbound_track') {
    return callType === 'Outgoing' ? 'agent' : 'customer'
  }
  if (track === 'outbound_track') {
    return callType === 'Outgoing' ? 'customer' : 'agent'
  }

  return 'customer'
}

/**
 * Append or update an utterance in the live utterances list.
 * If the last utterance is from the same speaker and was partial (not final),
 * it updates in place; otherwise appends a new utterance.
 * @param {Array<Object>} utterances
 * @param {{ speaker: string, text: string, isFinal?: boolean, timestamp?: string }} newUtterance
 * @returns {Array<Object>} Updated utterances array
 */
export function appendOrUpdateUtterance(utterances, newUtterance) {
  if (!newUtterance || !newUtterance.text) return utterances

  const speaker = (newUtterance.speaker || 'customer').toLowerCase()
  const isFinal = Boolean(newUtterance.isFinal)
  const text = newUtterance.text.trim()
  const timestamp = newUtterance.timestamp || new Date().toISOString()

  const list = [...utterances]
  const lastIndex = list.length - 1

  if (
    lastIndex >= 0 &&
    list[lastIndex].speaker === speaker &&
    !list[lastIndex].isFinal
  ) {
    list[lastIndex] = {
      ...list[lastIndex],
      text,
      isFinal,
    }
  } else {
    list.push({
      speaker,
      text,
      isFinal,
      timestamp,
    })
  }

  return list
}
