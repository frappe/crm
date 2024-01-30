<template>
  <div
    v-if="notificationsStore().visible"
    ref="target"
    class="absolute z-20 h-screen bg-white transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      'left': 'calc(100% + 1px)'
    }"
  >
    <div class="flex h-screen flex-col">
      <div
        class="z-20 flex items-center justify-between border-b bg-white px-5 py-2.5"
      >
        <div class="text-base font-medium">Notifications</div>
        <div class="flex gap-1">
          <Tooltip text="Mark all as read">
            <Button
              variant="ghost"
              @click="() => notificationsStore().mark_as_read.reload()"
            >
              <template #icon>
                <MarkAsDoneIcon class="h-4 w-4" />
              </template>
            </Button>
          </Tooltip>
          <Tooltip text="Close">
            <Button variant="ghost" @click="() => toggleNotificationPanel()">
              <template #icon>
                <FeatherIcon name="x" class="h-4 w-4" />
              </template>
            </Button>
          </Tooltip>
        </div>
      </div>
      <div
        v-if="notificationsStore().allNotifications?.length"
        class="divide-y overflow-auto text-base"
      >
        <RouterLink
          v-for="n in notificationsStore().allNotifications"
          :key="n.comment"
          :to="getRoute(n)"
          class="flex cursor-pointer items-start gap-2.5 px-4 py-2.5 hover:bg-gray-100"
          @click="mark_as_read(n.comment)"
        >
          <div class="mt-1 flex items-center gap-2.5">
            <div
              class="h-[5px] w-[5px] rounded-full"
              :class="[n.read ? 'bg-transparent' : 'bg-gray-900']"
            />
            <UserAvatar :user="n.from_user.name" size="lg" />
          </div>
          <div>
            <div class="mb-2 space-x-1 leading-5 text-gray-700">
              <span class="font-medium text-gray-900">
                {{ n.from_user.full_name }}
              </span>
              <span>mentioned you in {{ n.reference_doctype }}</span>
              <span class="font-medium text-gray-900">
                {{ n.reference_name }}
              </span>
            </div>
            <div class="text-sm text-gray-600">
              {{ timeAgo(n.creation) }}
            </div>
          </div>
        </RouterLink>
      </div>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-2"
      >
        <NotificationsIcon class="h-20 w-20 text-gray-300" />
        <div class="text-lg font-medium text-gray-500">
          No new notifications
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { notificationsStore } from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'
import { onClickOutside } from '@vueuse/core'
import { Tooltip } from 'frappe-ui'
import { ref } from 'vue'

const target = ref(null)
onClickOutside(
  target,
  () => {
    if (notificationsStore().visible) {
      toggleNotificationPanel()
    }
  },
  {
    ignore: ['#notifications-btn'],
  }
)

function toggleNotificationPanel() {
  notificationsStore().toggle()
}

function mark_as_read(comment) {
  notificationsStore().mark_comment_as_read(comment)
}

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
    hash: '#' + notification.comment,
  }
}
</script>
