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
import { ref } from 'vue'

/** CRM's built-in pages, in their default order. The sidebar items in FCRM Settings name them by route. */
export const navigationItems = [
  { label: 'Home', icon: LucideHouse, route: 'Home', desktopOnly: true },
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
  },
  { label: 'Leads', icon: LeadsIcon, route: 'Leads' },
  { label: 'Deals', icon: DealsIcon, route: 'Deals' },
  { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  { label: 'Organizations', icon: OrganizationsIcon, route: 'Organizations' },
  { label: 'Notes', icon: NoteIcon, route: 'Notes' },
  { label: 'Tasks', icon: TaskIcon, route: 'Tasks' },
  {
    label: 'Calendar',
    icon: CalendarIcon,
    route: 'Calendar',
    desktopOnly: true,
  },
  { label: 'Call Logs', icon: PhoneIcon, route: 'Call Logs' },
]

const builtInPages = Object.fromEntries(
  navigationItems.map((page) => [page.route, page]),
)

/** The session user's sidebar items from FCRM Settings, in order: the boot's, until the editor saves new ones. */
const savedSidebarItems = ref(null)

export function setSidebarItems(items) {
  savedSidebarItems.value = items
}

export function getNavigationItems({ mobile = false } = {}) {
  const sidebarItems = savedSidebarItems.value || window.sidebar_items || []
  // Empty only before the migrate that seeds FCRM Settings.
  const items = sidebarItems.length
    ? sidebarItems.map(toNavigationItem)
    : navigationItems
  return items.filter(
    (item) =>
      item.route &&
      router.hasRoute(item.route) &&
      (!mobile || !item.desktopOnly),
  )
}

/** The item's own icon, else its built-in page's icon. */
export function sidebarItemIcon(item) {
  return item.icon || builtInPages[item.route]?.icon || 'file-text'
}

/** A DocType item has no route until generic pages land, so the sidebar skips it. */
function toNavigationItem(item) {
  return {
    label: item.label,
    icon: sidebarItemIcon(item),
    route: item.route,
    desktopOnly: Boolean(builtInPages[item.route]?.desktopOnly),
  }
}
