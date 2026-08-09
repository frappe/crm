<template>
  <div class="space-y-3">
    <!-- LIST -->
    <template v-if="mode === 'list'">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex flex-wrap items-center gap-2">
          <label class="text-xs text-gray-500 dark:text-gray-400">Status:</label>
          <select
            v-model="statusFilter"
            class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            @change="page = 0; refetch()"
          >
            <option value="">All</option>
            <option value="Pending">Pending</option>
            <option value="Approved">Approved</option>
            <option value="Rejected">Rejected</option>
            <option value="Paid">Paid</option>
          </select>
        </div>
        <Button
          variant="solid"
          theme="blue"
          :disabled="!canCreate"
          :title="!canCreate ? 'You do not have permission to create' : ''"
          @click="canCreate && goNew()"
        >
          <template #prefix><FcIcon name="plus" :size="15" /></template>
          New
        </Button>
      </div>

      <FinanceTable
        :columns="columns"
        :rows="vouchers"
        :loading="loading"
        :error="error"
        empty-label="No rebate vouchers found."
        :page="page"
        :page-size="20"
        @update:page="p => { page = p; refetch() }"
        @row-click="goView"
        @retry="refetch"
      >
        <template #actions="{ row }">
          <div class="flex gap-1.5 flex-wrap">
            <template v-if="canApproveReject">
              <button
                v-if="row.status === 'Pending'"
                class="text-xs px-2.5 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors whitespace-nowrap"
                :disabled="actionPending === row.name"
                @click.stop="approveVoucher(row.name)"
              >Approve</button>
              <button
                v-if="row.status === 'Pending'"
                class="text-xs px-2.5 py-1 rounded border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors whitespace-nowrap"
                :disabled="actionPending === row.name"
                @click.stop="rejectVoucher(row.name)"
              >Reject</button>
            </template>
            <button
              v-if="canMarkPaid && row.status === 'Approved'"
              class="text-xs px-2.5 py-1 rounded bg-green-600 text-white hover:bg-green-700 transition-colors whitespace-nowrap"
              :disabled="actionPending === row.name"
              @click.stop="markPaid(row.name)"
            >Mark Paid</button>
          </div>
        </template>
      </FinanceTable>
    </template>

    <!-- VIEW -->
    <FinanceDetail
      v-else-if="mode === 'view'"
      doctype="CRM Partner Rebate Voucher"
      :name="activeName"
      @edit="goEdit"
      @deleted="onMutated"
      @close="goList"
    />

    <!-- NEW / EDIT -->
    <FinanceForm
      v-else-if="mode === 'new' || mode === 'edit'"
      doctype="CRM Partner Rebate Voucher"
      :name="mode === 'edit' ? activeName : null"
      @saved="onSaved"
      @close="goBackFromForm"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource, Button } from 'frappe-ui'
import FinanceTable from '../../components/FinanceTable.vue'
import FinanceForm from '../../components/crud/FinanceForm.vue'
import FinanceDetail from '../../components/crud/FinanceDetail.vue'
import FcIcon from '../../components/crud/FcIcon.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'
import { useBoot } from '../../composables/useBoot.js'

const { company } = useCompanyContext()
const { getRoles, isAdministrator } = useBoot()
const page = ref(0)
const statusFilter = ref('')
const actionPending = ref(null)

const mode = ref('list')
const activeName = ref(null)

// Gate arrays mirror the backend exactly:
//  - approve/reject_rebate_voucher -> Accounts User/Manager, Finance Manager, System Manager
//  - mark_rebate_paid              -> Finance Manager (+ admin) only
//  - DocType create perm           -> System Manager, Accounts Manager (+ Administrator)
const userRoles = getRoles()
const admin = isAdministrator()
const canApproveReject = admin || userRoles.some(r => ['Accounts User', 'Accounts Manager', 'Finance Manager', 'System Manager'].includes(r))
const canMarkPaid = admin || userRoles.some(r => ['Finance Manager', 'System Manager'].includes(r))
const canCreate = admin || userRoles.some(r => ['System Manager', 'Accounts Manager'].includes(r))

const columns = [
  { key: 'name', label: 'Voucher' },
  { key: 'partner', label: 'Partner' },
  { key: 'customer', label: 'Customer' },
  { key: 'rebate_pct', label: 'Rebate %', align: 'right' },
  { key: 'rebate_amount', label: 'Amount', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_rebate_vouchers',
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
const vouchers = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })

/* ---- Mode navigation ---- */
function goList() { mode.value = 'list'; activeName.value = null }
function goView(row) { activeName.value = row.name; mode.value = 'view' }
function goNew() { activeName.value = null; mode.value = 'new' }
function goEdit() { mode.value = 'edit' }
function goBackFromForm() { if (activeName.value) mode.value = 'view'; else goList() }
function onSaved(doc) {
  activeName.value = doc?.name || activeName.value
  refetch()
  mode.value = activeName.value ? 'view' : 'list'
}
function onMutated() { refetch(); goList() }

/* ---- Workflow actions ---- */
const approveRes = createResource({ url: 'crm.finance.api.approve_rebate_voucher' })
const rejectRes = createResource({ url: 'crm.finance.api.reject_rebate_voucher' })
const paidRes = createResource({ url: 'crm.finance.api.mark_rebate_paid' })

async function approveVoucher(name) {
  actionPending.value = name
  try { await approveRes.submit({ name, company: company.value }); resource.fetch() }
  finally { actionPending.value = null }
}
async function rejectVoucher(name) {
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
