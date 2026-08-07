<template>
  <div class="fc-assets space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Assets</h2>
    </div>

    <div class="flex gap-1 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        :class="[
          'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
          activeTab === tab.key
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300',
        ]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- Fixed Asset Register -->
    <div v-if="activeTab === 'register'">
      <FinanceTable
        :columns="assetCols"
        :rows="assetRows"
        :loading="assetLoading"
        :error="assetError"
        empty-label="No assets found."
        :page="assetPage"
        :page-size="20"
        @update:page="p => { assetPage = p; assetRes.fetch() }"
        @retry="assetRes.fetch()"
      />
    </div>

    <!-- Depreciation Schedule -->
    <div v-else-if="activeTab === 'depreciation'">
      <FinanceTable
        :columns="deprCols"
        :rows="deprRows"
        :loading="deprLoading"
        :error="deprError"
        empty-label="No depreciation schedules found."
        :page="deprPage"
        :page-size="20"
        @update:page="p => { deprPage = p; deprRes.fetch() }"
        @retry="deprRes.fetch()"
      />
    </div>

    <!-- Asset Movements -->
    <div v-else-if="activeTab === 'movements'">
      <FinanceTable
        :columns="moveCols"
        :rows="moveRows"
        :loading="moveLoading"
        :error="moveError"
        empty-label="No asset movements found."
        :page="movePage"
        :page-size="20"
        @update:page="p => { movePage = p; moveRes.fetch() }"
        @retry="moveRes.fetch()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceTable from '../components/FinanceTable.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const activeTab = ref('register')

const TABS = [
  { key: 'register', label: 'Fixed Asset Register' },
  { key: 'depreciation', label: 'Depreciation Schedule' },
  { key: 'movements', label: 'Asset Movements' },
]

// --- Fixed Asset Register ---
const assetPage = ref(0)
const assetCols = [
  { key: 'name', label: 'Asset' },
  { key: 'asset_name', label: 'Name' },
  { key: 'asset_category', label: 'Category' },
  { key: 'purchase_date', label: 'Purchase Date', type: 'date' },
  { key: 'gross_purchase_amount', label: 'Cost', type: 'currency', align: 'right' },
  { key: 'accumulated_depreciation_amount', label: 'Accum. Depr.', type: 'currency', align: 'right' },
  { key: 'value_after_depreciation', label: 'Net Book Value', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]
const assetRes = createResource({
  url: 'crm.finance.api.get_assets',
  makeParams() { return { company: company.value, page: assetPage.value, page_size: 20 } },
  auto: true,
})
const assetRows = computed(() => assetRes.data || [])
const assetLoading = computed(() => assetRes.loading)
const assetError = computed(() => assetRes.error)

// --- Depreciation Schedule ---
const deprPage = ref(0)
const deprCols = [
  { key: 'asset', label: 'Asset' },
  { key: 'schedule_date', label: 'Schedule Date', type: 'date' },
  { key: 'depreciation_amount', label: 'Amount', type: 'currency', align: 'right' },
  { key: 'depreciation_method', label: 'Method' },
  { key: 'fiscal_year', label: 'Fiscal Year' },
]
const deprRes = createResource({
  url: 'crm.finance.api.get_depreciation_schedule',
  makeParams() { return { company: company.value, page: deprPage.value, page_size: 20 } },
  auto: false,
})
const deprRows = computed(() => deprRes.data || [])
const deprLoading = computed(() => deprRes.loading)
const deprError = computed(() => deprRes.error)

// --- Asset Movements ---
const movePage = ref(0)
const moveCols = [
  { key: 'name', label: 'Movement' },
  { key: 'transaction_date', label: 'Date', type: 'date' },
  { key: 'purpose', label: 'Purpose' },
]
const moveRes = createResource({
  url: 'crm.finance.api.get_asset_movements',
  makeParams() { return { company: company.value, page: movePage.value, page_size: 20 } },
  auto: false,
})
const moveRows = computed(() => moveRes.data || [])
const moveLoading = computed(() => moveRes.loading)
const moveError = computed(() => moveRes.error)

watch(activeTab, (t) => {
  if (t === 'depreciation' && !deprRes.data) deprRes.fetch()
  if (t === 'movements' && !moveRes.data) moveRes.fetch()
})

watch(company, () => {
  assetPage.value = 0; assetRes.fetch()
  if (activeTab.value === 'depreciation') { deprPage.value = 0; deprRes.fetch() }
  if (activeTab.value === 'movements') { movePage.value = 0; moveRes.fetch() }
})
</script>
