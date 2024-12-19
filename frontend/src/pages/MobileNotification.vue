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
      <Tooltip :text="__('Mark all as read')">
        <div>
          <Button
            :label="__('Mark all as read')"
            @click="() => mark_as_read.reload()"
          >
            <template #prefix>
              <MarkAsDoneIcon class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </Tooltip>
    </template>
  </LayoutHeader>
  <div class="flex flex-col overflow-hidden text-ink-gray-9">
    <div
      v-if="notifications.data?.length"
      class="divide-y divide-outline-gray-1 overflow-y-auto text-base"
    >
      <RouterLink
        v-for="n in notifications.data"
        :key="n.comment"
        :to="getRoute(n)"
        class="flex cursor-pointer items-start gap-3 px-2.5 py-3 hover:bg-surface-gray-2"
        @click="mark_doc_as_read(n.comment || n.notification_type_doc)"
      >
        <div class="mt-1 flex items-center gap-2.5">
          <div
            class="size-[5px] rounded-full"
            :class="[n.read ? 'bg-transparent' : 'bg-surface-gray-7']"
          />
          <WhatsAppIcon v-if="n.type == 'WhatsApp'" class="size-7" />
          <UserAvatar v-else :user="n.from_user.name" size="lg" />
        </div>
        <div>
          <div v-if="n.notification_text" v-html="n.notification_text" />
          <div v-else class="mb-2 space-x-1 leading-5 text-ink-gray-5">
            <span class="font-medium text-ink-gray-9">
              {{ n.from_user.full_name }}
            </span>
            <span>
              {{ __('mentioned you in {0}', [n.reference_doctype]) }}
            </span>
            <span class="font-medium text-ink-gray-9">
              {{ n.reference_name }}
            </span>
          </div>
          <div class="text-sm text-ink-gray-5">
            {{ __(timeAgo(n.creation)) }}
          </div>
        </div>
      </RouterLink>
    </div>
    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2">
      <NotificationsIcon class="h-20 w-20 text-ink-gray-2" />
      <div class="text-lg font-medium text-ink-gray-4">
        {{ __('No new notifications') }}
      </div>
    </div>
  </div>
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { notifications, notificationsStore } from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'
import { Breadcrumbs, Tooltip } from 'frappe-ui'
import { onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, mark_doc_as_read } = notificationsStore()

onBeforeUnmount(() => {
  $socket.off('crm_notification')
})

onMounted(() => {
  $socket.on('crm_notification', () => {
    notifications.reload()
  })
})

function getRoute(notification) {
  let params = {
    leadId: notification.reference_name,
  }
  if (notification.route_name === 'Deal') {
    params = {
      dealId: notification.reference_name,
    }
  }
  return {
    name: notification.route_name,
    params: params,
    hash: '#' + notification.comment || notification.notification_type_doc,
  }
}
</script>
