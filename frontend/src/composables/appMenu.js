import FrappeCloudIcon from '@/components/Icons/FrappeCloudIcon.vue'
import AppsIcon from '@/components/Icons/AppsIcon.vue'
import {
  showSettings,
  activeSettingsPage,
  isMobileView,
} from '@/composables/settings'
import { showAboutModal } from '@/composables/modals'
import { confirmLoginToFrappeCloud } from '@/composables/frappecloud'
import { useCloudSettings } from '@/composables/cloudSettings'
import CreditCardIcon from '~icons/lucide/credit-card'
import { spriteIcon } from '@/utils/spriteIcon'
import { sanitizeHTML } from '@/utils'
import { createResource } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'

const DOCS_URL = 'https://docs.frappe.io/crm'

/**
 * The menu under the app logo, built from FCRM Settings' `dropdown_items` rows.
 * `getItems` returns the rows, so the sidebar and the App menu settings preview
 * build the same menu from saved and unsaved rows.
 */
export function useAppMenu(getItems) {
  const { available: canManageBilling, open: openBilling } = useCloudSettings()

  const apps = createResource({
    url: 'frappe.apps.get_apps',
    cache: 'apps',
    auto: true,
    transform: (data) => [deskApp(), ...crmSiblingApps(data)],
  })

  const groups = computed(() => {
    const _groups = [{ group: '', hideLabel: true, options: [] }]
    for (const item of getItems() || []) {
      if (item.hidden) continue
      if (item.type === 'Separator') {
        _groups.push({ group: '', hideLabel: true, options: [] })
      } else {
        _groups.at(-1).options.push(menuOption(item))
      }
    }
    // A separator with nothing after it must not draw a trailing divider.
    return _groups.filter((group) => group.options.length)
  })

  function menuOption(item) {
    const icon = menuItemIcon(item)
    if (item.is_standard) return standardOption(item, icon)
    return {
      icon,
      label: __(item.label),
      onClick: () => {
        const route = safeRoute(item.route)
        if (route) window.open(route, item.open_in_new_window ? '_blank' : '')
      },
    }
  }

  function standardOption(item, icon) {
    const label = __(item.label)
    switch (item.name1) {
      case 'app_selector':
        return { icon, label, submenu: appSubmenu() }
      case 'settings':
        return {
          icon,
          label,
          onClick: openGeneralSettings,
          condition: () => !isMobileView.value,
        }
      case 'login_to_fc':
        if (canManageBilling) {
          return {
            icon: markRaw(CreditCardIcon),
            label: __('Manage Billing'),
            onClick: () => openBilling(),
            condition: () => !isMobileView.value,
          }
        }
        return {
          icon,
          label,
          onClick: () => confirmLoginToFrappeCloud(),
          condition: () => !isMobileView.value && window.is_fc_site,
        }
      case 'help':
        return { icon, label, submenu: helpSubmenu() }
    }
  }

  function helpSubmenu() {
    return [
      {
        icon: spriteIcon('book-open'),
        label: __('Documentation'),
        onClick: () => window.open(DOCS_URL, '_blank', 'noopener'),
      },
      {
        icon: spriteIcon('info'),
        label: __('About'),
        onClick: () => (showAboutModal.value = true),
      },
    ]
  }

  function appSubmenu() {
    return (apps.data || []).map((app) => ({
      label: app.title,
      onClick: () => (window.location.href = app.route),
      slots: {
        prefix: () => h('img', { class: 'size-5 rounded-4', src: app.logo }),
      },
    }))
  }

  return { groups }
}

/** The icon a menu row shows: a built-in's own, a lucide name, or a saved SVG. */
export function menuItemIcon(item) {
  if (item.is_standard && item.name1 === 'app_selector')
    return markRaw(AppsIcon)
  if (item.is_standard && item.name1 === 'login_to_fc') {
    return markRaw(FrappeCloudIcon)
  }
  const icon = item.icon || 'external-link'
  if (icon.startsWith('<svg')) {
    return markRaw(h('div', { innerHTML: sanitizeHTML(icon) }))
  }
  return spriteIcon(icon)
}

/** The link as an absolute http(s) URL, or '' for anything else, such as `javascript:`. */
export function safeRoute(route) {
  if (typeof route !== 'string' || !route) return ''
  try {
    const url = new URL(route, window.location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : ''
  } catch {
    return ''
  }
}

function openGeneralSettings() {
  activeSettingsPage.value = __('General')
  showSettings.value = true
}

function deskApp() {
  return {
    name: 'frappe',
    logo: '/assets/frappe/images/framework.png',
    title: __('Desk'),
    route: '/desk',
  }
}

function crmSiblingApps(data) {
  return data
    .filter((app) => app.name !== 'crm')
    .map((app) => ({
      name: app.name,
      logo: app.logo,
      title: __(app.title),
      route: app.route,
    }))
}
