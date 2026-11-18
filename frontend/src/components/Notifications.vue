<template>
  <div
    v-if="visible"
    ref="target"
    class="absolute z-20 h-screen bg-surface-base transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '400px',
      'min-width': '400px',
      left: 'calc(100% + 1px)',
    }"
  >
    <div class="flex h-screen flex-col text-ink-gray-9">
      <div class="flex justify-between items-center">
        <div class="text-lg-medium text-ink-gray-8 px-4 pt-[15px] pb-3">
          {{ __('Notifications') }}
        </div>
        <div class="flex gap-1 mr-3">
          <Button
            v-if="notifications.data?.length"
            :tooltip="__('Mark all as read')"
            :icon="MarkAsDoneIcon"
            variant="ghost"
            @click="markAllAsRead"
          />
        </div>
      </div>
      <NotificationFilters v-model:read="read" v-model:category="category" />
      <div class="flex h-full">
        <div
          v-if="shownGroups.length"
          class="w-full divide-y divide-outline-elevation-2 overflow-auto text-base"
        >
          <NotificationRow
            v-for="group in shownGroups"
            :key="group.key"
            :group="group"
            @click="markAsRead(group.docs)"
          />
        </div>
        <EmptyState
          v-else
          :title="
            notifications.data?.length
              ? __('Nothing Here')
              : __('No New Notifications')
          "
          :description="
            notifications.data?.length
              ? __('No notifications match these filters')
              : __('You have no new notifications')
          "
          :icon="NotificationsIcon"
          width="lg"
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import NotificationFilters from '@/components/NotificationFilters.vue'
import NotificationRow from '@/components/NotificationRow.vue'
import {
  visible,
  notifications,
  notificationsStore,
} from '@/stores/notifications'
import { useEventNotificationAlert } from '@/data/notifications'
import { globalStore } from '@/stores/global'
import { groupNotifications, notificationCategory } from '@/utils/notifications'
import { onClickOutside, useEventListener } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, toggle, mark_doc_as_read } = notificationsStore()
const { handleEventNotification } = useEventNotificationAlert()
const { capture } = useTelemetry()

const read = ref('all')
const category = ref('')

const groups = computed(() => groupNotifications(notifications.data || []))
const shownGroups = computed(() =>
  groups.value.filter(
    (g) =>
      (read.value === 'all' || g.unread) &&
      (!category.value || notificationCategory(g.latest) === category.value),
  ),
)

const target = ref(null)
// An open menu makes the page inert, so its dismiss click lands outside the
// panel; the menu is gone by click time, so note it on pointerdown.
let menuWasOpen = false
useEventListener(
  window,
  'pointerdown',
  () => (menuWasOpen = !!document.querySelector("[role='menu']")),
  { capture: true },
)

onClickOutside(
  target,
  () => {
    if (menuWasOpen) return
    if (visible.value) toggle()
  },
  {
    ignore: ['#notifications-btn'],
  },
)

function markAsRead(docs) {
  capture('notification_mark_as_read')
  mark_doc_as_read(docs)
}

function markAllAsRead() {
  capture('notification_mark_all_as_read')
  mark_as_read.reload()
}

onBeforeUnmount(() => {
  $socket.off('crm_notification')
  $socket.off('event_notification')
})

onMounted(() => {
  $socket.on('crm_notification', () => notifications.reload())
  $socket.on('event_notification', (data) => handleEventNotification(data))
})
</script>
