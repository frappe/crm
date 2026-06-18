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
      <!-- <TabButtons
        v-model="activeTab"
        :buttons="tabs"
        class="flex px-4 pt-3 pb-0.5 [&_button]:w-full [&_div]:w-full"
      /> -->
      <!-- <div v-show="activeTab == 'all'" class="flex flex-1 min-h-0"> -->
      <NotificationPanel
        class="w-full"
        app-name="crm"
        :current-user="currentUser"
        :socket="$socket"
        :show-close="false"
        :title="__('Notifications')"
        :icon="resolveIcon"
        :tabs="tabs"
        @item-click="onItemClick"
        @update:unread-count="onUnreadCount"
      >
        <template #empty>
          <EmptyState
            title="No New Notifications"
            description="You have no new notifications"
            :icon="NotificationsIcon"
            width="lg"
          />
        </template>
      </NotificationPanel>
      <!-- </div> -->
      <!-- <div v-if="activeTab == 'events'" class="flex flex-1 min-h-0">
        <EventNotificationsArea />
      </div> -->
    </div>
  </div>
</template>
<script setup lang="ts">
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import EventNotificationsArea from '@/components/EventNotificationsArea.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import {
  visible,
  frameworkUnreadCount,
  notificationsStore,
} from '@/stores/notifications'
import { useEventNotificationAlert } from '@/data/notifications'
import { globalStore } from '@/stores/global'
import { sessionStore } from '@/stores/session'
import { onClickOutside } from '@vueuse/core'
import { useTelemetry } from 'frappe-ui/frappe'
import { TabButtons } from 'frappe-ui'
import { NotificationPanel } from '@framework/ui/components/Notifications'
import type { NotificationTab } from '@framework/ui/components/Notifications'
import { markRaw, ref, onMounted, onBeforeUnmount } from 'vue'
import router from '@/router'

const { $socket } = globalStore()
const { user: currentUser } = sessionStore()
const { toggle } = notificationsStore()
const { handleEventNotification } = useEventNotificationAlert()
const { capture } = useTelemetry()

// const activeTab = ref('all')
const tabs: NotificationTab[] = [
  { label: __('All'), filters: {}, count: (n) => n.length },
  { label: __('Unread'), filterFn: (n) => !n.read, count: 'unread' },
]

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

function onUnreadCount(count) {
  frameworkUnreadCount.value = count
}

const WhatsAppRawIcon = markRaw(WhatsAppIcon)

// leading visual per row: WhatsApp glyph for WhatsApp notifications, sender avatar otherwise
function resolveIcon(n) {
  if (n.type === 'WhatsApp') return WhatsAppRawIcon
  return undefined
}

function onItemClick(n) {
  capture('notification_mark_as_read')
  const route = getRoute(n)
  if (route) router.push(route)
  else if (n.link) window.location.href = n.link
  toggle()
}

// map a Notification Log row to a CRM SPA route when it references a Lead/Deal
function getRoute(n) {
  const doctype = n.reference_doctype || n.document_type
  const name = n.reference_name || n.document_name
  if (!name) return null
  if (doctype === 'CRM Deal') {
    return { name: 'Deal', params: { dealId: name }, hash: n.hash || '' }
  }
  if (doctype === 'CRM Lead') {
    return { name: 'Lead', params: { leadId: name }, hash: n.hash || '' }
  }
  return null
}

onBeforeUnmount(() => {
  $socket.off('event_notification')
})

onMounted(() => {
  $socket.on('event_notification', (data) => handleEventNotification(data))
})
</script>
