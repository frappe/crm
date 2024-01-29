import { defineStore } from 'pinia'
import { sessionStore } from '@/stores/session'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const notificationsStore = defineStore('crm-notifications', () => {
  const { user } = sessionStore()

  let visible = ref(false)
  let unreadNotifications = reactive([])
  let allNotifications = reactive([])

  const notifications = createResource({
    url: 'crm.api.notifications.get_notifications',
    initialData: [],
    auto: true,
    transform(data) {
      allNotifications = data
      unreadNotifications = data.filter((d) => !d.read)
      return data
    },
  })

  function toggle() {
    visible.value = !visible.value
  }

  function getUnreadNotifications() {
    return unreadNotifications || []
  }

  function getAllNotifications() {
    return allNotifications || []
  }

  return {
    visible,
    toggle,
    getAllNotifications,
    getUnreadNotifications,
  }
})
