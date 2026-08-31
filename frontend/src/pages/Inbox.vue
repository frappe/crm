<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Inbox'), route: { name: 'Inbox' } }]" />
    </template>
    <template #right-header>
      <Button
        variant="ghost"
        icon="lucide-refresh-cw"
        :loading="conversations.loading"
        @click="conversations.reload()"
      />
    </template>
  </LayoutHeader>
  <div class="flex-1 overflow-y-auto">
    <div
      v-if="conversations.data?.length"
      class="mx-auto flex w-full max-w-3xl flex-col divide-y divide-outline-gray-1 px-3 py-2 sm:px-5"
    >
      <div
        v-for="row in conversations.data"
        :key="row.reference_doctype + row.reference_name"
        class="flex cursor-pointer items-center gap-3 rounded px-2 py-3 hover:bg-surface-gray-1"
        @click="openConversation(row)"
      >
        <Avatar
          size="lg"
          :label="row.title"
          :image="row.image"
          class="shrink-0"
        />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="truncate text-base font-medium text-ink-gray-9">
              {{ row.title }}
            </span>
            <Badge
              :label="row.channel"
              :theme="row.channel == 'WhatsApp' ? 'green' : 'blue'"
              size="sm"
            />
          </div>
          <div class="mt-0.5 truncate text-sm text-ink-gray-5">
            <span v-if="row.type == 'Outgoing'" class="text-ink-gray-4">
              {{ __('You') }}:
            </span>
            {{ row.message }}
          </div>
        </div>
        <div class="shrink-0 text-xs text-ink-gray-4">
          <Tooltip :text="formatDate(row.creation)">
            <span>{{ timeAgo(row.creation) }}</span>
          </Tooltip>
        </div>
      </div>
    </div>
    <div
      v-else-if="!conversations.loading"
      class="flex h-full flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <SMSIcon class="h-8 w-8" />
      <span class="text-lg font-medium">{{ __('No Conversations Found') }}</span>
      <span class="text-sm">
        {{ __('Incoming and outgoing SMS/WhatsApp threads will appear here.') }}
      </span>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import { formatDate, timeAgo } from '@/utils'
import { globalStore } from '@/stores/global'
import { createResource, Breadcrumbs, Avatar, Tooltip } from 'frappe-ui'
import { onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { $socket } = globalStore()

const conversations = createResource({
  url: 'crm.api.inbox.get_conversations',
  cache: 'inbox-conversations',
  auto: true,
})

function openConversation(row) {
  const routeName = row.reference_doctype == 'CRM Lead' ? 'Lead' : 'Deal'
  const paramKey = routeName == 'Lead' ? 'leadId' : 'dealId'
  const hash = row.channel == 'WhatsApp' ? '#whatsapp' : '#sms'
  router.push({
    name: routeName,
    params: { [paramKey]: row.reference_name },
    hash,
  })
}

function reloadOnMessage() {
  conversations.reload()
}

onMounted(() => {
  $socket.on('crm_sms_message', reloadOnMessage)
  $socket.on('whatsapp_message', reloadOnMessage)
})

onBeforeUnmount(() => {
  $socket.off('crm_sms_message', reloadOnMessage)
  $socket.off('whatsapp_message', reloadOnMessage)
})
</script>
