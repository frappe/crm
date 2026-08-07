<template>
  <div class="fc-dashboard-charts space-y-6 mt-6">
    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="n in 4" :key="n" class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 h-48 animate-pulse" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-sm text-red-500 py-2">
      Failed to load chart data. <button class="underline" @click="refetch">Retry</button>
    </div>

    <!-- Charts grid -->
    <div v-else-if="chartData" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Cashflow: full-width on mobile, spans 2 cols on md -->
      <div class="md:col-span-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <CashflowChart :data="chartData.cashflow" />
      </div>

      <!-- AR Aging -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <ArAgingChart :data="chartData.ar_aging" />
      </div>

      <!-- AP Aging (hidden for AR Accountant — API omits it) -->
      <div v-if="chartData.ap_aging" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <ApAgingChart :data="chartData.ap_aging" />
      </div>

      <!-- P&L Summary -->
      <div :class="['bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4', !chartData.ap_aging ? 'md:col-span-1' : '']">
        <PlSummaryBar :data="chartData.pl" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import CashflowChart from './charts/CashflowChart.vue'
import ArAgingChart from './charts/ArAgingChart.vue'
import ApAgingChart from './charts/ApAgingChart.vue'
import PlSummaryBar from './charts/PlSummaryBar.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const props = defineProps({
  period: { type: String, default: 'month' },
})

const { company } = useCompanyContext()

const resource = createResource({
  url: 'crm.finance.api.get_dashboard_charts',
  makeParams() {
    return { company: company.value, period: props.period }
  },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const chartData = computed(() => resource.data || null)

function refetch() { resource.fetch() }

watch(company, () => resource.fetch())
watch(() => props.period, () => resource.fetch())
</script>
