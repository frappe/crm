<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          { label: __('Notifications'), route: { name: 'Notifications' } },
        ]"
      />
    </template>
    <template #right-header>
      <Button
        :tooltip="__('Mark all as read')"
        :label="__('Mark all as read')"
        :iconLeft="MarkAsDoneIcon"
        @click="() => mark_as_read.reload()"
      />
    </template>
  </LayoutHeader>
  <div class="flex flex-col overflow-hidden text-ink-gray-9">
    <div
      v-if="notifications.data?.length"
      class="divide-y divide-outline-gray-1 overflow-y-auto text-base"
    >
      <NotificationRow
        v-for="group in groups"
        :key="group.key"
        :group="group"
        @click="mark_doc_as_read(group.docs)"
      />
    </div>
    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2">
      <NotificationsIcon class="h-20 w-20 text-ink-gray-2" />
      <div class="text-lg-medium text-ink-gray-4">
        {{ __('No New Notifications') }}
      </div>
    </div>
  </div>
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import NotificationRow from '@/components/NotificationRow.vue'
import { notifications, notificationsStore } from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { groupNotifications } from '@/utils/notifications'
import { Breadcrumbs } from 'frappe-ui'
import { computed, onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, mark_doc_as_read } = notificationsStore()

const groups = computed(() => groupNotifications(notifications.data || []))

onBeforeUnmount(() => {
  $socket.off('crm_notification')
})

onMounted(() => {
  $socket.on('crm_notification', () => {
    notifications.reload()
  })
})
</script>
