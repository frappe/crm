<template>
  <div
    v-if="!isSidebarCollapsed"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-modal text-base"
  >
    <div class="inline-flex text-ink-gray-9 gap-2 items-center font-medium">
      <FeatherIcon class="h-4" name="info" />
      {{ __('Sales Hierarchy') }}
    </div>
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})
</script>
