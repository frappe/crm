<template>
  <div class="space-y-3">
    <!-- HRMS not installed guard -->
    <div
      v-if="hrmsNotInstalled"
      class="flex flex-col items-center justify-center py-12 gap-3 text-gray-400 dark:text-gray-500"
    >
      <LucideAlertCircle class="w-10 h-10" />
      <p class="text-base font-semibold text-gray-600 dark:text-gray-300">HRMS Not Installed</p>
      <p class="text-sm">Expense Claims and Employee Advances require the HRMS app.</p>
    </div>

    <template v-else>
      <div class="flex flex-wrap items-center gap-2">
        <label class="text-xs text-gray-500 dark:text-gray-400">Status:</label>
        <select
          v-model="statusFilter"
          class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          @change="page = 0; refetch()"
        >
          <option value="">Approved (unpaid)</option>
          <option value="all">All</option>
          <option value="Draft">Draft</option>
          <option value="Approved">Approved</option>
          <option value="Rejected">Rejected</option>
        </select>
      </div>

      <FinanceTable
        :columns="columns"
        :rows="claims"
        :loading="loading"
        :error="error"
        empty-label="No expense claims found."
        :page="page"
        :page-size="20"
        @update:page="p => { page = p; refetch() }"
        @retry="refetch"
      >
        <template #actions="{ row }">
          <button
            v-if="!row.is_paid"
            class="text-xs px-2.5 py-1 rounded bg-green-600 text-white hover:bg-green-700 transition-colors whitespace-nowrap"
            :disabled="markingPaid === row.name"
            @click.stop="markAsPaid(row.name)"
          >{{ markingPaid === row.name ? 'Saving…' : 'Mark Paid' }}</button>
          <span
            v-else
            class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
          >Paid</span>
        </template>
      </FinanceTable>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import LucideAlertCircle from '~icons/lucide/alert-circle'
import FinanceTable from '../../components/FinanceTable.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const page = ref(0)
const statusFilter = ref('')
const markingPaid = ref(null)

const columns = [
  { key: 'name', label: 'Claim' },
  { key: 'employee_name', label: 'Employee' },
  { key: 'department', label: 'Department' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'total_sanctioned_amount', label: 'Amount', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_expense_claims',
  makeParams() {
    const filters = []
    if (statusFilter.value && statusFilter.value !== 'all') {
      filters.push(['status', '=', statusFilter.value])
    } else if (!statusFilter.value) {
      filters.push(['status', '=', 'Approved'])
      filters.push(['is_paid', '=', 0])
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
const rawData = computed(() => resource.data || { items: [], hrms_not_installed: false })
const hrmsNotInstalled = computed(() => !!rawData.value.hrms_not_installed)
const claims = computed(() => rawData.value.items || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })

const markPaidResource = createResource({ url: 'crm.finance.api.mark_expense_claim_paid' })

async function markAsPaid(name) {
  markingPaid.value = name
  try {
    await markPaidResource.submit({ name })
    resource.fetch()
  } finally {
    markingPaid.value = null
  }
}
</script>
