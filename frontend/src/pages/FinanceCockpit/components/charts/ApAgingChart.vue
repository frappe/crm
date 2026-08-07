<template>
  <div class="fc-ap-aging-chart">
    <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">AP Aging</h3>
    <div v-if="!data || !data.length" class="h-32 flex items-center justify-center text-sm text-gray-400">No data</div>
    <div v-else class="space-y-2">
      <div v-for="(bucket, i) in data" :key="bucket.bucket" class="flex items-center gap-2">
        <span class="text-xs text-gray-500 dark:text-gray-400 w-14 flex-shrink-0">{{ bucket.bucket }}</span>
        <div class="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden">
          <div
            :class="['h-full rounded transition-all duration-500', COLOR_CLASSES[i] || 'bg-gray-400']"
            :style="{ width: barWidth(bucket.amount) }"
          />
        </div>
        <span class="text-xs font-medium text-gray-700 dark:text-gray-300 w-20 text-right flex-shrink-0">
          {{ formatNum(bucket.amount) }}
        </span>
      </div>
    </div>
    <div class="flex flex-wrap gap-3 mt-3 text-xs text-gray-500 dark:text-gray-400">
      <span v-for="(b, i) in data" :key="b.bucket" class="flex items-center gap-1">
        <span :class="['inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0', COLOR_CLASSES[i] || 'bg-gray-400']" />
        {{ b.bucket }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })

const COLOR_CLASSES = [
  'bg-emerald-500',
  'bg-amber-400',
  'bg-orange-500',
  'bg-red-500',
]

const maxAmount = computed(() => Math.max(...(props.data || []).map(b => b.amount), 1))

function barWidth(amount) {
  return (amount / maxAmount.value * 100).toFixed(1) + '%'
}

function formatNum(n) {
  if (n == null) return '—'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K'
  return n.toFixed(0)
}
</script>
