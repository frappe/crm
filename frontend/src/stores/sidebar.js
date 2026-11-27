import { navigationItems } from '@/utils/navigation'
import { ref } from 'vue'

/** The standard sidebar, for a site whose boot has none (before the migrate that adds CRM Sidebar). */
const STANDARD_ITEMS = [
  ...navigationItems.map((page) => ({
    key: page.key,
    type: 'Link',
    label: page.label,
    link_type: 'Built-in',
    link_to: page.route,
  })),
  {
    key: 'public_views',
    type: 'Section',
    label: 'Public Views',
    collapsible: 1,
  },
  {
    key: 'pinned_views',
    type: 'Section',
    label: 'Pinned Views',
    collapsible: 1,
  },
]

/** The merged sidebar the session user sees, from the boot and then from each save. */
export const sidebarItems = ref(window.crm_sidebar || STANDARD_ITEMS)
