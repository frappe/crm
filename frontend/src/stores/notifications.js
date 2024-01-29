import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

export const notificationsStore = defineStore('crm-notifications', () => {
  let visible = ref(false)

  const notifications = createResource({
    url: 'crm.api.notifications.get_notifications',
    initialData: [],
    auto: true,
  })

  const mark_as_read = createResource({
    url: 'crm.api.notifications.mark_as_read',
    auto: false,
    onSuccess: () => notifications.reload(),
  })

  function toggle() {
    visible.value = !visible.value
  }

  const allNotifications = computed(() => notifications.data || [])

  function mark_comment_as_read(comment) {
    mark_as_read.params = { comment: comment }
    mark_as_read.reload()
    toggle()
  }

  return {
    visible,
    allNotifications,
    mark_as_read,
    mark_comment_as_read,
    toggle,
  }
})
