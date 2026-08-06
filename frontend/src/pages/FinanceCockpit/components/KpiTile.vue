<template>
  <div
    class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-1 cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 transition-colors min-w-0"
    @click="$emit('click')"
  >
    <div class="flex items-center justify-between">
      <span class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide truncate">{{ label }}</span>
      <span class="w-6 h-6 flex-shrink-0 text-gray-400 dark:text-gray-500" v-html="iconSvg" />
    </div>
    <div class="text-2xl font-bold text-gray-900 dark:text-gray-100 truncate">
      {{ formattedValue }}
    </div>
    <div class="flex items-center gap-1 text-xs" v-if="deltaPct !== 0">
      <span
        :class="deltaDirection === 'up' ? 'text-green-500' : deltaDirection === 'down' ? 'text-red-500' : 'text-gray-400'"
        v-html="deltaIcon"
      />
      <span :class="deltaDirection === 'up' ? 'text-green-500' : deltaDirection === 'down' ? 'text-red-500' : 'text-gray-400'">
        {{ Math.abs(deltaPct) }}%
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  currency: { type: String, default: '' },
  deltaPct: { type: Number, default: 0 },
  deltaDirection: { type: String, default: 'neutral' },
  iconSvg: { type: String, default: '' },
})
defineEmits(['click'])

const formattedValue = computed(() => {
  const v = props.value ?? 0
  if (v >= 1_000_000) return (props.currency ? props.currency + ' ' : '') + (v / 1_000_000).toFixed(1) + 'M'
  if (v >= 1_000) return (props.currency ? props.currency + ' ' : '') + (v / 1_000).toFixed(1) + 'K'
  return (props.currency ? props.currency + ' ' : '') + v.toLocaleString(undefined, { maximumFractionDigits: 0 })
})

const deltaIcon = computed(() => {
  if (props.deltaDirection === 'up') {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>'
  }
  if (props.deltaDirection === 'down') {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>'
  }
  return ''
})
</script>
