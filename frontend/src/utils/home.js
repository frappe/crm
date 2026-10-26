export function greetingFor(date, name) {
  const greeting = greetingAt(date.getHours())
  return name ? `${greeting}, ${name}` : greeting
}

function greetingAt(hour) {
  if (hour < 12) return __('Good morning')
  if (hour < 17) return __('Good afternoon')
  return __('Good evening')
}

// Home rows stay static so they can hold buttons; a stretched link opens them,
// so they need the clickable row surface by hand.
export const homeRowClass =
  'rounded-[10px] hover:bg-surface-gray-1 active:bg-surface-gray-2 has-[:focus-visible]:bg-surface-gray-2'

export function recordRoute({ doctype, name }) {
  return doctype === 'CRM Deal'
    ? { name: 'Deal', params: { dealId: name } }
    : { name: 'Lead', params: { leadId: name } }
}

export function recordListViews(doctype = 'Both') {
  const views = {
    Lead: { label: __('Leads'), route: { name: 'Leads' } },
    Deal: { label: __('Deals'), route: { name: 'Deals' } },
  }
  return doctype === 'Both' ? [views.Lead, views.Deal] : [views[doctype]]
}

export function recordTitle({ title, subtitle, name }) {
  return {
    title: title || subtitle || name,
    subtitle: title && subtitle !== title ? subtitle : '',
  }
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
