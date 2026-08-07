<template>
  <div class="space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <label class="text-xs text-gray-500 dark:text-gray-400">Status:</label>
      <select
        v-model="statusFilter"
        class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
        @change="page = 0; refetch()"
      >
        <option value="">Unpaid + Partly Paid</option>
        <option value="all">All</option>
        <option value="Unpaid">Unpaid</option>
        <option value="Partly Paid">Partly Paid</option>
        <option value="Draft">Draft (Pending Approval)</option>
      </select>
    </div>

    <FinanceTable
      :columns="columns"
      :rows="invoices"
      :loading="loading"
      :error="error"
      empty-label="No purchase invoices found."
      :page="page"
      :page-size="20"
      @update:page="p => { page = p; refetch() }"
      @retry="refetch"
    >
      <template #actions="{ row }">
        <button
          v-if="row.status === 'Draft'"
          class="text-xs px-2.5 py-1 rounded bg-green-600 text-white hover:bg-green-700 transition-colors whitespace-nowrap disabled:opacity-60"
          :disabled="!isFinanceManager || approvingRow === row.name"
          :title="!isFinanceManager ? 'Finance Manager only' : ''"
          @click.stop="isFinanceManager && approvePurchaseInvoice(row)"
        >{{ approvingRow === row.name ? 'Approving...' : 'Approve' }}</button>
        <a
          :href="'/app/payment-entry/new-payment-entry-1?party_type=Supplier&party=' + encodeURIComponent(row.supplier)"
          target="_blank"
          class="text-xs px-2.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors whitespace-nowrap"
          @click.stop
        >Pay</a>
      </template>
    </FinanceTable>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceTable from '../../components/FinanceTable.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const page = ref(0)
const statusFilter = ref('')
const approvingRow = ref(null)

const isFinanceManager = computed(() => {
  try {
    return (window.frappe?.boot?.user?.roles || []).includes('Finance Manager')
  } catch {
    return false
  }
})

const columns = [
  { key: 'name', label: 'Invoice' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'due_date', label: 'Due', type: 'date' },
  { key: 'outstanding_amount', label: 'Outstanding', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_ap_invoices',
  makeParams() {
    const isDraft = statusFilter.value === 'Draft'
    const filters = []
    if (!isDraft && statusFilter.value && statusFilter.value !== 'all') {
      filters.push(['status', '=', statusFilter.value])
    }
    return {
      company: company.value,
      filters: JSON.stringify(filters),
      include_draft: isDraft ? 1 : 0,
      page: page.value,
      page_size: 20,
    }
  },
  auto: true,
})

const approveResource = createResource({
  url: 'crm.finance.api.approve_purchase_invoice',
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const invoices = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })

async function approvePurchaseInvoice(row) {
  approvingRow.value = row.name
  try {
    await approveResource.fetch({ name: row.name })
    refetch()
  } finally {
    approvingRow.value = null
  }
}
</script>
