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
        <option value="Reported">Reported</option>
        <option value="Confirmed">Confirmed</option>
        <option value="Rejected">Rejected</option>
        <option value="Paid">Paid</option>
      </select>
    </div>

    <FinanceTable
      :columns="columns"
      :rows="commissions"
      :loading="loading"
      :error="error"
      empty-label="No commission records found."
      :page="page"
      :page-size="20"
      @update:page="p => { page = p; refetch() }"
      @retry="refetch"
    >
      <template #actions="{ row }">
        <div class="flex gap-1.5 flex-wrap">
          <template v-if="canConfirmReject">
            <button
              v-if="row.status === 'Reported'"
              class="text-xs px-2.5 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors whitespace-nowrap"
              :disabled="actionPending === row.name"
              @click.stop="confirmCommission(row.name)"
            >Confirm</button>
            <button
              v-if="row.status === 'Reported'"
              class="text-xs px-2.5 py-1 rounded border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors whitespace-nowrap"
              :disabled="actionPending === row.name"
              @click.stop="rejectCommission(row.name)"
            >Reject</button>
          </template>
          <button
            v-if="canMarkPaid && row.status === 'Confirmed'"
            class="text-xs px-2.5 py-1 rounded bg-green-600 text-white hover:bg-green-700 transition-colors whitespace-nowrap"
            :disabled="actionPending === row.name"
            @click.stop="markPaid(row.name)"
          >Mark Paid</button>
        </div>
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
const actionPending = ref(null)

const userRoles = window.frappe?.boot?.user?.roles ?? []
const canConfirmReject = userRoles.some(r => ['Accounts User', 'Accounts Manager', 'Finance Manager', 'System Manager'].includes(r))
const canMarkPaid = userRoles.some(r => ['Finance Manager', 'System Manager'].includes(r))

const columns = [
  { key: 'name', label: 'Commission' },
  { key: 'sales_person', label: 'Sales Person' },
  { key: 'customer', label: 'Customer' },
  { key: 'commission_pct', label: 'Commission %', align: 'right' },
  { key: 'commission_amount', label: 'Amount', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_sales_commissions',
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
const commissions = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })

const confirmRes = createResource({ url: 'crm.finance.api.confirm_commission' })
const rejectRes = createResource({ url: 'crm.finance.api.reject_commission' })
const paidRes = createResource({ url: 'crm.finance.api.mark_commission_paid' })

async function confirmCommission(name) {
  actionPending.value = name
  try { await confirmRes.submit({ name, company: company.value }); resource.fetch() }
  finally { actionPending.value = null }
}
async function rejectCommission(name) {
  actionPending.value = name
  try { await rejectRes.submit({ name, company: company.value }); resource.fetch() }
  finally { actionPending.value = null }
}
async function markPaid(name) {
  actionPending.value = name
  try { await paidRes.submit({ name, company: company.value }); resource.fetch() }
  finally { actionPending.value = null }
}
</script>
