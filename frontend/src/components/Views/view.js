import { computed, h } from 'vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import { useViews } from '@/stores/view'
import { sidebarLayouts } from '@/doctype/generateRoutes.js'

const { pinnedViews, publicViews } = useViews()

export const iconMap = {
  Dashboard: LucideLayoutDashboard,
  Leads: LeadsIcon,
  Deals: DealsIcon,
  Contacts: ContactsIcon,
  Organizations: OrganizationsIcon,
  Notes: NoteIcon,
  Tasks: TaskIcon,
  Calendar: CalendarIcon,
  'Call Logs': PhoneIcon,
}

export const links = computed(() => {
  const staticLinks = Object.keys(iconMap).map((key) => {
    return {
      label: key,
      icon: iconMap[key],
      to: key,
    }
  })

  if (!sidebarLayouts.value?.length) {
    return staticLinks
  }

  return sidebarLayouts.value.map((link) => {
    return {
      label: link.label || link.doctype || link.routeName,
      icon: iconMap[link.label || link.routeName] || link.icon,
      to: link.routeName || link.doctype + ' List',
    }
  })
})

export const allViews = computed(() => {
  const viewGroups = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links.value.filter((link) => {
        if (link.condition) {
          return link.condition()
        }
        return true
      }),
    },
  ]

  if (publicViews.value?.length) {
    viewGroups.push({
      name: 'Public views',
      opened: true,
      views: parseView(publicViews.value),
    })
  }

  if (pinnedViews.value?.length) {
    viewGroups.push({
      name: 'Pinned views',
      opened: true,
      views: parseView(pinnedViews.value),
    })
  }

  return viewGroups
})

export function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewName: view.name },
      },
    }
  })
}

export function getIcon(routeName, icon) {
  if (icon) {
    return h('div', { class: 'size-auto' }, icon)
  }

  return iconMap[routeName] || PinIcon
}
