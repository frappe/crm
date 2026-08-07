<template>
  <div class="fc-scoped-view space-y-4">
    <!-- Read-only notice -->
    <div class="flex items-center gap-2 px-4 py-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
      <LucideInfo class="w-4 h-4 text-blue-500 shrink-0" />
      <span class="text-sm text-blue-700 dark:text-blue-300">You have read-only access to your partners' rebate records.</span>
    </div>

    <!-- Rebate KPI tile -->
    <div v-if="kpiData" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-1">
        <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <LucideHandCoins class="w-4 h-4" />
          <span class="text-xs uppercase tracking-wide">Pending Rebate Liability</span>
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {{ formatCurrency(kpiData.pending_rebates?.value, kpiData.pending_rebates?.currency) }}
        </div>
      </div>
    </div>
    <div v-else-if="kpiLoading" class="h-24 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />

    <!-- Section header -->
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">My Partners' Rebates</h2>
    </div>

    <!-- Rebate vouchers table (read-only) -->
    <FinanceTable
      :columns="columns"
      :rows="vouchers"
      :loading="vouchersLoading"
      empty-label="No rebate vouchers found for your partners."
    />
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import LucideInfo from '~icons/lucide/info'
import LucideHandCoins from '~icons/lucide/hand-coins'
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

const vouchersResource = createResource({
  url: 'crm.finance.api.get_rebate_vouchers',
  makeParams() { return { company: company.value, page_size: 50 } },
  auto: true,
})
const vouchers = computed(() => vouchersResource.data || [])
const vouchersLoading = computed(() => vouchersResource.loading)

watch(company, () => {
  kpiResource.fetch()
  vouchersResource.fetch()
})

const columns = [
  { key: 'name', label: 'Voucher #' },
  { key: 'partner', label: 'Partner' },
  { key: 'deal', label: 'Deal' },
  { key: 'customer', label: 'Customer' },
  { key: 'rebate_amount', label: 'Amount', align: 'right', type: 'currency' },
  { key: 'status', label: 'Status', type: 'status' },
]

const { formatCurrency } = useCurrency()
</script>
