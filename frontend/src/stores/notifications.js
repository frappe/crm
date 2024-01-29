import { defineStore } from 'pinia'
import { sessionStore } from '@/stores/session'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const notificationsStore = defineStore('crm-notifications', () => {
  const { user } = sessionStore()

  let visible = ref(false)
  let unreadNotifications = reactive([])

  const notifications = createResource({
    url: 'crm.api.notifications.get_notifications',
    cache: 'crm-notifications',
    initialData: [],
    auto: true,
    transform(data) {
      unreadNotifications = data
      return data
    },
  })

  function toggle() {
    visible.value = !visible.value
  }

  function getUnreadNotifications() {
    return unreadNotifications || []
  }

  return {
    visible,
    toggle,
    getUnreadNotifications,
  }
})
