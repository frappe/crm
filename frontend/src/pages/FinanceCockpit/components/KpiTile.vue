<template>
  <div
    class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4 flex flex-col gap-2 cursor-pointer hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all min-w-0"
    @click="$emit('click')"
  >
    <div class="flex items-start justify-between gap-2">
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400 leading-tight">{{ label }}</span>
      <span
        class="w-8 h-8 flex-shrink-0 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-500 dark:text-gray-300"
        v-html="iconSvg"
      />
    </div>
    <div class="text-2xl font-bold text-gray-900 dark:text-gray-100 tabular-nums truncate">
      {{ formattedValue }}
    </div>
    <div class="flex items-center gap-1 text-xs" v-if="deltaPct !== 0">
      <span
        :class="deltaDirection === 'up' ? 'text-green-500' : deltaDirection === 'down' ? 'text-red-500' : 'text-gray-400'"
        v-html="deltaIcon"
      />
      <span :class="deltaDirection === 'up' ? 'text-green-500' : deltaDirection === 'down' ? 'text-red-500' : 'text-gray-400'">
        {{ Math.abs(deltaPct) }}% vs last period
      </span>
    </div>
    <div v-else class="text-xs text-gray-400 dark:text-gray-500">—</div>
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
  const prefix = props.currency ? props.currency + ' ' : ''
  if (v >= 1_000_000) return prefix + (v / 1_000_000).toFixed(1) + 'M'
  if (v >= 1_000)     return prefix + (v / 1_000).toFixed(1) + 'K'
  return prefix + v.toLocaleString(undefined, { maximumFractionDigits: 0 })
})

const deltaIcon = computed(() => {
  if (props.deltaDirection === 'up') {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>'
  }
  if (props.deltaDirection === 'down') {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>'
  }
  return ''
})
</script>
