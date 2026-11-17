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
      <div class="flex h-full">
        <div
          v-if="notifications.data?.length"
          class="w-full overflow-auto p-1.5 text-base"
        >
          <NotificationRow
            v-for="group in groups"
            :key="group.key"
            :group="group"
            @click="markAsRead(group.docs)"
          />
        </div>
        <EmptyState
          v-else
          :title="__('No New Notifications')"
          :description="__('You have no new notifications')"
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
import NotificationRow from '@/components/NotificationRow.vue'
import {
  visible,
  notifications,
  notificationsStore,
} from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { groupNotifications } from '@/utils/notifications'
import { onClickOutside } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, toggle, mark_doc_as_read } = notificationsStore()
const { capture } = useTelemetry()

const groups = computed(() => groupNotifications(notifications.data || []))

const target = ref(null)
onClickOutside(
  target,
  () => {
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
})

onMounted(() => {
  $socket.on('crm_notification', () => notifications.reload())
})
</script>
