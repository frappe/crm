import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'
import { formatCompactNumber } from '@/utils/numberFormat.js'

export const visible = ref(false)

// The list holds only the latest notifications, so the unread badge comes from
// its own count, refreshed whenever the list is.
const unreadCount = createResource({
  url: 'crm.api.notifications.get_unread_count',
  initialData: 0,
})

export const notifications = createResource({
  url: 'crm.api.notifications.get_notifications',
  initialData: [],
  auto: true,
  onSuccess: () => unreadCount.reload(),
})

export const unreadNotificationsCount = computed(() => {
  const count = unreadCount.data || 0
  return count ? formatCompactNumber(count) : 0
})

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
