export function greetingFor(date, name) {
  const greeting = greetingAt(date.getHours())
  return name ? `${greeting}, ${name}` : greeting
}

function greetingAt(hour) {
  if (hour < 12) return __('Good morning')
  if (hour < 17) return __('Good afternoon')
  return __('Good evening')
}

export function recordRoute({ doctype, name }) {
  return doctype === 'CRM Deal'
    ? { name: 'Deal', params: { dealId: name } }
    : { name: 'Lead', params: { leadId: name } }
}

export function taskRecordRoute(task) {
  return recordRoute({
    doctype: task.reference_doctype,
    name: task.reference_docname,
  })
}

export function recordListRoute(doctype = 'Both') {
  return { name: doctype === 'Deal' ? 'Deals' : 'Leads' }
}

export function recordTitle({ title, subtitle, name }) {
  return title || subtitle || name
}

// "<1m", "45m", "3h 20m", "2d 4h"
export function shortDuration(seconds) {
  if (seconds == null) return ''
  const minutes = Math.floor(seconds / 60)
  if (minutes < 1) return '<1m'
  const units = [
    ['d', Math.floor(minutes / 1440)],
    ['h', Math.floor(minutes / 60) % 24],
    ['m', minutes % 60],
  ]
  const first = units.findIndex(([, value]) => value)
  return units
    .slice(first, first + 2)
    .filter(([, value]) => value)
    .map(([unit, value]) => `${value}${unit}`)
    .join(' ')
}

// Number columns are right aligned and start with the highest first.
export function nextSort(sort, column) {
  if (sort.key === column.key) return { ...sort, descending: !sort.descending }
  return { key: column.key, descending: column.align === 'right' }
}

// Rows without a value go last in either direction.
export function sortRows(rows, { descending }, valueOf) {
  const direction = descending ? -1 : 1
  return [...rows].sort((a, b) => {
    const [first, second] = [valueOf(a), valueOf(b)]
    if (first == null || second == null) {
      return (first == null) - (second == null)
    }
    return (
      direction *
      (typeof first === 'string' ? first.localeCompare(second) : first - second)
    )
  })
}

// A percentage over a near-empty start says nothing past "much more"; the arrow carries the sign.
export function formatPercentChange(value) {
  return value > 999 ? '999+' : String(Math.round(value))
}
