<template>
  <div class="fc-pl-summary">
    <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">P&amp;L Summary</h3>
    <div v-if="!data" class="h-24 flex items-center justify-center text-sm text-gray-400">No data</div>
    <div v-else class="space-y-3">
      <div class="space-y-2">
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500 dark:text-gray-400 w-20 flex-shrink-0">Income</span>
          <div class="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden">
            <div class="h-full rounded bg-green-500 transition-all duration-500"
              :style="{ width: incomeWidth }" />
          </div>
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300 w-20 text-right flex-shrink-0">{{ fmt(data.income) }}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500 dark:text-gray-400 w-20 flex-shrink-0">Expenses</span>
          <div class="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden">
            <div class="h-full rounded bg-red-400 transition-all duration-500"
              :style="{ width: expensesWidth }" />
          </div>
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300 w-20 text-right flex-shrink-0">{{ fmt(data.expenses) }}</span>
        </div>
      </div>
      <div class="pt-2 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span class="text-xs text-gray-500 dark:text-gray-400">Net</span>
        <span :class="['text-sm font-bold', data.net >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400']">
          {{ fmt(data.net) }}
        </span>
      </div>
      <p class="text-xs text-gray-400">{{ data.period_label }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Object, default: null } })

const maxVal = computed(() => Math.max(props.data?.income ?? 0, props.data?.expenses ?? 0, 1))

const incomeWidth = computed(() => ((props.data?.income ?? 0) / maxVal.value * 100).toFixed(1) + '%')
const expensesWidth = computed(() => ((props.data?.expenses ?? 0) / maxVal.value * 100).toFixed(1) + '%')

function fmt(n) {
  if (n == null) return '—'
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(0) + 'K'
  return n.toFixed(0)
}
</script>
