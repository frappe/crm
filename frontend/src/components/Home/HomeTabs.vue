<template>
  <TabButtons v-model="tab" :options="tabs">
    <template #suffix="{ button }">
      <span
        v-if="counts[button.value]"
        class="text-sm tabular-nums text-ink-gray-5"
      >
        {{ counts[button.value] }}
      </span>
    </template>
  </TabButtons>
</template>
<script setup>
import { TabButtons } from 'frappe-ui'

defineProps({
  tabs: { type: Array, required: true },
  counts: { type: Object, default: () => ({}) },
})

const tab = defineModel({ type: String, required: true })
</script>
