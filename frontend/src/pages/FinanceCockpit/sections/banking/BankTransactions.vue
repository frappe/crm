<template>
  <div class="space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <label class="text-xs text-gray-500 dark:text-gray-400">Status:</label>
      <select
        v-model="statusFilter"
        class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
        @change="page = 0; refetch()"
      >
        <option value="">All</option>
        <option value="Unreconciled">Unreconciled</option>
        <option value="Reconciled">Reconciled</option>
      </select>
    </div>

    <FinanceTable
      :columns="columns"
      :rows="transactions"
      :loading="loading"
      :error="error"
      empty-label="No bank transactions found."
      :page="page"
      :page-size="20"
      @update:page="p => { page = p; refetch() }"
      @retry="refetch"
    >
      <template #actions="{ row }">
        <a
          :href="'/app/bank-reconciliation-tool?bank_account=' + encodeURIComponent(row.bank_account)"
          target="_blank"
          class="text-xs px-2.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors whitespace-nowrap"
          @click.stop
        >Reconcile</a>
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
  { key: 'name', label: 'Transaction' },
  { key: 'date', label: 'Date', type: 'date' },
  { key: 'bank_account', label: 'Account' },
  { key: 'description', label: 'Description' },
  { key: 'deposit', label: 'Deposit', type: 'currency', align: 'right' },
  { key: 'withdrawal', label: 'Withdrawal', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_bank_transactions',
  makeParams() {
    const filters = []
    if (statusFilter.value) filters.push(['status', '=', statusFilter.value])
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
const transactions = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
