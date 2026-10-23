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
