<template>
  <div
    v-if="notificationsStore().visible"
    ref="target"
    class="fixed z-20 h-screen overflow-auto bg-white transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      left: isSidebarCollapsed ? '3rem' : '14rem',
    }"
  >
    <div
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-5 py-2.5"
    >
      <span class="text-lg font-medium">Notifications</span>
      <span>
        <Button
          theme="blue"
          variant="ghost"
          @click="() => notificationsStore().mark_as_read.reload()"
        >
          <template #icon>
            <MarkAsDoneIcon class="h-4 w-4" />
          </template>
        </Button>
        <Button
          theme="gray"
          variant="ghost"
          @click="() => toggleNotificationPanel()"
        >
          <template #icon>
            <FeatherIcon name="x" class="h-4 w-4" />
          </template>
        </Button>
      </span>
    </div>
    <div class="divide-y text-base">
      <RouterLink
        v-for="n in notificationsStore().allNotifications"
        :key="n.comment"
        :to="getRoute(n)"
        class="flex cursor-pointer items-start gap-3.5 px-5 py-2.5 hover:bg-gray-100"
        @click="mark_as_read(n.comment)"
      >
        <UserAvatar :user="n.from_user.name" size="md" />
        <span>
          <div class="mb-2 leading-5">
            <span class="space-x-1 text-gray-700">
              <span class="font-medium text-gray-900">
                {{ n.from_user.full_name }}
              </span>
              <span>mentioned you in {{ n.reference_doctype }}</span>
              <span class="font-medium text-gray-900">
                {{ n.reference_name }}
              </span>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <div class="text-sm text-gray-600">
              {{ timeAgo(n.creation) }}
            </div>
            <div v-if="!n.read" class="h-1.5 w-1.5 rounded-full bg-gray-900" />
          </div>
        </span>
      </RouterLink>
    </div>
  </div>
</template>
<script setup>
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { notificationsStore } from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'
import { onClickOutside } from '@vueuse/core'
import { ref, computed } from 'vue'

const isSidebarCollapsed = computed(() => globalStore().isSidebarCollapsed)

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
