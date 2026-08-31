<template>
  <div>
    <div
      v-for="sms in messages"
      :key="sms.name"
      class="activity group mb-3 flex gap-2"
      :class="sms.type == 'Outgoing' ? 'flex-row-reverse' : ''"
    >
      <div
        :id="sms.name"
        class="relative max-w-[90%] rounded-md p-1.5 pl-2 text-base shadow-sm"
        :class="
          sms.type == 'Outgoing'
            ? 'bg-surface-gray-2 text-ink-gray-9'
            : 'bg-surface-gray-1 text-ink-gray-9'
        "
      >
        <Badge
          v-if="['Failed', 'Undelivered'].includes(sms.status)"
          theme="red"
          :label="__(sms.status)"
          class="absolute -top-2 right-0"
        />
        <div class="whitespace-pre-wrap break-words">{{ sms.message }}</div>
        <div
          class="mt-1 flex items-center justify-end gap-1 text-xs text-ink-gray-4"
        >
          <Tooltip :text="formatDate(sms.creation)">
            <span>{{ timeAgo(sms.creation) }}</span>
          </Tooltip>
          <span v-if="sms.type == 'Outgoing'">· {{ __(sms.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { formatDate, timeAgo } from '@/utils'
import { Tooltip } from 'frappe-ui'

defineProps({
  messages: { type: Array, default: () => [] },
})
</script>
