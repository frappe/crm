<template>
  <div class="space-y-3">
    <!-- Status filter -->
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
      </select>
    </div>

    <FinanceTable
      :columns="columns"
      :rows="invoices"
      :loading="loading"
      :error="error"
      empty-label="No invoices found."
      :page="page"
      :page-size="20"
      @update:page="p => { page = p; refetch() }"
      @retry="refetch"
    >
      <template #actions="{ row }">
        <a
          :href="'/app/payment-entry/new-payment-entry-1?party_type=Customer&party=' + encodeURIComponent(row.customer)"
          target="_blank"
          class="text-xs px-2.5 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors whitespace-nowrap"
          @click.stop
        >Record Payment</a>
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

const columns = [
  { key: 'name', label: 'Invoice' },
  { key: 'customer', label: 'Customer' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'due_date', label: 'Due', type: 'date' },
  { key: 'outstanding_amount', label: 'Outstanding', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_ar_invoices',
  makeParams() {
    const filters = []
    if (statusFilter.value && statusFilter.value !== 'all') {
      filters.push(['status', '=', statusFilter.value])
    } else if (!statusFilter.value) {
      filters.push(['status', 'in', ['Unpaid', 'Partly Paid']])
    }
    return {
      company: company.value,
      filters: JSON.stringify(filters),
      page: page.value,
      page_size: 20,
    }
  },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const invoices = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
