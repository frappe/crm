import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import LucideHouse from '~icons/lucide/house'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import router from '@/router'

export const navigationItems = [
  {
    key: 'home',
    label: 'Home',
    icon: LucideHouse,
    route: 'Home',
    desktopOnly: true,
  },
  {
    key: 'dashboard',
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
  },
  { key: 'leads', label: 'Leads', icon: LeadsIcon, route: 'Leads' },
  { key: 'deals', label: 'Deals', icon: DealsIcon, route: 'Deals' },
  { key: 'contacts', label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  {
    key: 'organizations',
    label: 'Organizations',
    icon: OrganizationsIcon,
    route: 'Organizations',
  },
  { key: 'notes', label: 'Notes', icon: NoteIcon, route: 'Notes' },
  { key: 'tasks', label: 'Tasks', icon: TaskIcon, route: 'Tasks' },
  {
    key: 'calendar',
    label: 'Calendar',
    icon: CalendarIcon,
    route: 'Calendar',
    desktopOnly: true,
  },
  { key: 'call_logs', label: 'Call Logs', icon: PhoneIcon, route: 'Call Logs' },
]

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter(
    (item) => router.hasRoute(item.route) && (!mobile || !item.desktopOnly),
  )
}

export const DOCTYPE_ICON = 'table'

/** The built-in page a sidebar item opens, when its key names one. */
export function builtInPage(item) {
  return item.link_type === 'Built-in'
    ? navigationItems.find((page) => page.key === item.key)
    : undefined
}

/**
 * Where a DocType item goes. Null until the generic list page has a route
 * (frappe/crm#3648), so the sidebar leaves DocType items out for now.
 */
export function doctypeRoute() {
  return null
}

/**
 * The merged sidebar as the main list and its sections. `items` come from
 * `crm.api.sidebar.get_sidebar`, already filtered for the user; a built-in page
 * also needs its route and, on mobile, must not be desktop only.
 */
export function getSidebarLayout(items, { mobile = false } = {}) {
  const linkOf = (item) => sidebarLink(item, mobile)
  const main = items
    .filter((item) => item.type !== 'Section' && !item.parent_key)
    .map(linkOf)
    .filter(Boolean)
  const sections = items
    .filter((item) => item.type === 'Section')
    .map((section) => ({
      key: section.key,
      label: section.label,
      collapsible: Boolean(section.collapsible),
      opened: !(section.collapsible && section.keep_closed),
      fillsFrom:
        section.key === 'public_views' || section.key === 'pinned_views'
          ? section.key
          : null,
      links: items
        .filter((item) => item.parent_key === section.key)
        .map(linkOf)
        .filter(Boolean),
    }))
  return { main, sections }
}

function sidebarLink(item, mobile) {
  const page = builtInPage(item)
  if (page) {
    if (!router.hasRoute(page.route) || (mobile && page.desktopOnly))
      return null
    return {
      key: page.route,
      label: item.label || page.label,
      icon: item.icon || page.icon,
      to: { name: page.route },
    }
  }
  const to = item.link_type === 'DocType' && doctypeRoute(item.link_to)
  if (!to) return null
  return {
    key: item.key,
    label: item.label || item.link_to,
    icon: item.icon || DOCTYPE_ICON,
    to,
  }
}
