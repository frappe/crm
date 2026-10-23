export function greetingFor(date, name) {
  const hour = date.getHours()
  const greeting =
    hour < 12
      ? __('Good morning')
      : hour < 17
        ? __('Good afternoon')
        : __('Good evening')
  return name ? `${greeting}, ${name}` : greeting
}

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

// A deal without an organization falls back to its contact name, then its ID.
export function recordTitle({ title, subtitle, name }) {
  return {
    title: title || subtitle || name,
    subtitle: title && subtitle !== title ? subtitle : '',
  }
}

// The two largest units, for averages where seconds are noise: "<1m", "45m", "3h 20m", "2d 4h".
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
