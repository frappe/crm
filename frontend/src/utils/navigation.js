import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import FileSpreadsheetIcon from '@/components/Icons/FileSpreadsheetIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import router from '@/router'

export const navigationSections = [
  {
    name: 'Data',
    collapsible: true,
    items: [
      { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
      { label: 'Organizations', icon: OrganizationsIcon, route: 'Organizations' },
      { label: 'Import', icon: FileSpreadsheetIcon, route: 'Data Imports' },
      { label: 'Daily Allocation', icon: CalendarIcon, route: 'Daily Allocation' },
    ],
  },
  {
    name: 'Outreach',
    collapsible: true,
    items: [{ label: 'My Task', icon: TaskIcon, route: 'Tasks' }],
  },
  {
    name: 'Sales Pipeline',
    collapsible: true,
    items: [
      { label: 'Leads', icon: LeadsIcon, route: 'Leads' },
      { label: 'Deals', icon: DealsIcon, route: 'Deals' },
    ],
  },
]

export const navigationItems = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    route: 'Dashboard',
    desktopOnly: true,
  },
  { label: 'Contacts', icon: ContactsIcon, route: 'Contacts' },
  { label: 'Organizations', icon: OrganizationsIcon, route: 'Organizations' },
  { label: 'Import', icon: FileSpreadsheetIcon, route: 'Data Imports' },
  { label: 'Daily Allocation', icon: CalendarIcon, route: 'Daily Allocation' },
  { label: 'My Task', icon: TaskIcon, route: 'Tasks' },
  { label: 'Leads', icon: LeadsIcon, route: 'Leads' },
  { label: 'Deals', icon: DealsIcon, route: 'Deals' },
  { label: 'Call Logs', icon: PhoneIcon, route: 'Call Logs' },
]

export function getNavigationItems({ mobile = false } = {}) {
  return navigationItems.filter(
    (item) => router.hasRoute(item.route) && (!mobile || !item.desktopOnly),
  )
}

export function getNavigationSections({ mobile = false } = {}) {
  return navigationSections.map((section) => ({
    ...section,
    items: section.items.filter(
      (item) => router.hasRoute(item.route) && (!mobile || !item.desktopOnly),
    ),
  }))
}
