export const LANDING_PAGE_KEY = 'crm_landing_page'

export function getLandingPage() {
  return window.sysdefaults?.[LANDING_PAGE_KEY] || 'Home'
}

export function setLandingPageLocally(page) {
  window.sysdefaults = { ...window.sysdefaults, [LANDING_PAGE_KEY]: page }
}

export function landingRoute(page, views, hasRoute) {
  if (!page || page === 'Home') return null
  const view = views?.find((v) => v.name === page)
  if (view) return viewRoute(view)
  return hasRoute(page) ? { name: page } : null
}

export function viewRoute({ route_name, type, name, is_standard }) {
  route_name = route_name || 'Leads'
  if (name && !is_standard) {
    return {
      name: route_name,
      params: { viewType: type },
      query: { view: name },
    }
  }
  return { name: route_name, params: { viewType: type } }
}

export function landingViews(views, user) {
  return (views || []).filter(
    (v) => !v.is_standard && (v.user === user || v.public || v.pinned),
  )
}
