<template>
  <div class="fc-scoped-view space-y-4">
    <!-- Read-only notice -->
    <div class="flex items-center gap-2 px-4 py-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
      <LucideInfo class="w-4 h-4 text-blue-500 shrink-0" />
      <span class="text-sm text-blue-700 dark:text-blue-300">You have read-only access to your team's commission records.</span>
    </div>

    <!-- Commission KPI tile -->
    <div v-if="kpiData" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-1">
        <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <LucideDollarSign class="w-4 h-4" />
          <span class="text-xs uppercase tracking-wide">Unpaid Commissions</span>
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {{ formatCurrency(kpiData.unpaid_commissions?.value, kpiData.unpaid_commissions?.currency) }}
        </div>
      </div>
    </div>
    <div v-else-if="kpiLoading" class="h-24 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />

    <!-- Section header -->
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">My Team's Commissions</h2>
    </div>

    <!-- Commissions table (read-only) -->
    <FinanceTable
      :columns="columns"
      :rows="commissions"
      :loading="commissionsLoading"
      empty-label="No commissions found for your team."
    />
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import LucideInfo from '~icons/lucide/info'
import LucideDollarSign from '~icons/lucide/dollar-sign'
import FinanceTable from '../components/FinanceTable.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'
import { useCurrency } from '../composables/useCurrency.js'

const { company } = useCompanyContext()

const kpiResource = createResource({
  url: 'crm.finance.api.get_finance_kpis',
  makeParams() { return { company: company.value } },
  auto: true,
})
const kpiData = computed(() => kpiResource.data || null)
const kpiLoading = computed(() => kpiResource.loading)

const commissionsResource = createResource({
  url: 'crm.finance.api.get_sales_commissions',
  makeParams() { return { company: company.value, page_size: 50 } },
  auto: true,
})
const commissions = computed(() => commissionsResource.data || [])
const commissionsLoading = computed(() => commissionsResource.loading)

watch(company, () => {
  kpiResource.fetch()
  commissionsResource.fetch()
})

const columns = [
  { key: 'name', label: 'Commission #' },
  { key: 'sales_person', label: 'Sales Person' },
  { key: 'deal', label: 'Deal' },
  { key: 'customer', label: 'Customer' },
  { key: 'commission_amount', label: 'Amount', align: 'right', type: 'currency' },
  { key: 'status', label: 'Status', type: 'status' },
]

const { formatCurrency } = useCurrency()
</script>
