import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

export const visible = ref(false)

export const notifications = createResource({
  url: 'crm.api.notifications.get_notifications',
  initialData: [],
  auto: true,
})

export const unreadNotificationsCount = computed(
  () => notifications.data?.filter((n) => !n.read).length || 0,
)

// Unread count for the framework Notification Log feed (shown by NotificationPanel on
// desktop). Kept separate from the CRM Notification feed above so mobile, which still
// renders the CRM feed, is unaffected. Updated via the panel's @update:unread-count while
// it is open; seeded (and refreshed on realtime) by the resource below so the sidebar
// badge is correct even before the panel is opened.
export const frameworkUnreadCount = ref(0)

const frameworkUnreadResource = createResource({
  url: 'frappe.client.get_count',
  // Notification Log is permission-scoped to the logged-in user (for_user), matching the
  // panel's own scoping. `app: 'crm'` mirrors the panel's app-name="crm".
  params: {
    doctype: 'Notification Log',
    filters: { read: 0, app: 'crm' },
  },
  auto: true,
  onSuccess: (count) => (frameworkUnreadCount.value = count || 0),
})

export function reloadFrameworkUnreadCount() {
  frameworkUnreadResource.reload()
}

export const notificationsStore = defineStore('crm-notifications', () => {
  const mark_as_read = createResource({
    url: 'crm.api.notifications.mark_as_read',
    onSuccess: () => {
      mark_as_read.params = {}
      notifications.reload()
    },
  })

  function toggle() {
    visible.value = !visible.value
  }

  function mark_doc_as_read(doc) {
    mark_as_read.params = { doc: doc }
    mark_as_read.reload()
    toggle()
  }

  return {
    unreadNotificationsCount,
    mark_as_read,
    mark_doc_as_read,
    toggle,
  }
})
