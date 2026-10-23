// The leads and deals a user opened last, kept in their browser only.
// Read by the command palette and the Recently opened Home widget.

const RECENT_TYPES = { Lead: 'CRM Lead', Deal: 'CRM Deal' }
export const RECENT_LIMIT = 5

export function rememberRoute(route, user) {
  const doctype = RECENT_TYPES[route.name]
  if (!doctype) return
  const param = `${route.name.toLowerCase()}Id`
  const name = route.params[param]
  if (!name) return
  const recent = [
    { doctype, name },
    ...readRecent(user).filter(
      (item) => item.doctype !== doctype || item.name !== name,
    ),
  ].slice(0, RECENT_LIMIT)
  localStorage.setItem(recentKey(user), JSON.stringify(recent))
}

// Newest first across doctypes, e.g. [{ doctype: 'CRM Deal', name: 'D-1' }].
export function readRecent(user) {
  try {
    const recent = JSON.parse(localStorage.getItem(recentKey(user)) || '[]')
    return Array.isArray(recent) ? recent : []
  } catch {
    return []
  }
}

export function recentNamesByDoctype(recent) {
  const names = {}
  for (const { doctype, name } of recent) {
    names[doctype] = [...(names[doctype] || []), name]
  }
  return names
}

export function sortByRecency(records, recent) {
  const position = (record) =>
    recent.findIndex(
      (item) => item.doctype === record.doctype && item.name === record.name,
    )
  return [...records].sort((a, b) => position(a) - position(b))
}

function recentKey(user) {
  return `crm-command-palette-recent:${user || 'anonymous'}`
}
