<template>
  <div>
    <div
      v-for="whatsapp in messages"
      :key="whatsapp.name"
      class="flex"
      :class="{ 'justify-end': whatsapp.type == 'Outgoing' }"
    >
      <div
        class="mb-3 inline-flex max-w-[90%] gap-2 rounded-md bg-gray-50 p-2 text-base shadow-sm"
      >
        <div>{{ whatsapp.message }}</div>
        <div class="-mb-1 flex items-end gap-1 text-gray-600 shrink-0">
          <Tooltip :text="dateFormat(whatsapp.creation, 'ddd, MMM D, YYYY')">
            <div class="text-2xs">{{ dateFormat(whatsapp.creation, 'hh:mm a') }}</div>
          </Tooltip>
          <div v-if="whatsapp.type == 'Outgoing'">
            <CheckIcon v-if="whatsapp.status == 'sent'" class="size-4" />
            <DoubleCheckIcon
              v-else-if="['read', 'delivered'].includes(whatsapp.status)"
              class="size-4"
              :class="{ 'text-blue-500': whatsapp.status == 'read' }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import { Tooltip } from 'frappe-ui'
import { dateFormat } from '@/utils'

const props = defineProps({
  messages: Array,
})
</script>
