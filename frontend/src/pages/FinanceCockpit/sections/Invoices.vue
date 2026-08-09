<template>
  <CrudSection
    ref="sectionRef"
    doctype="Sales Invoice"
    title="Invoices"
    list-resource-url="crm.finance.api.get_ar_invoices"
    :list-params="listParams"
    :columns="columns"
    :create-from="createFrom"
    empty-label="No invoices found."
  >
    <template #filters>
      <label class="text-xs text-ink-gray-5">Status:</label>
      <select
        v-model="statusFilter"
        class="text-xs border border-outline-gray-2 rounded px-2 py-1 bg-surface-white text-ink-gray-7"
        @change="onFilterChange"
      >
        <option value="">Unpaid + Partly Paid</option>
        <option value="all">All</option>
        <option value="Unpaid">Unpaid</option>
        <option value="Partly Paid">Partly Paid</option>
        <option value="Overdue">Overdue</option>
        <option value="Paid">Paid</option>
      </select>
    </template>
  </CrudSection>
</template>

<script setup>
import { ref } from 'vue'
import CrudSection from '../components/crud/CrudSection.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const statusFilter = ref('')
const sectionRef = ref(null)

const columns = [
  { key: 'name',             label: 'Invoice' },
  { key: 'customer',         label: 'Customer' },
  { key: 'posting_date',     label: 'Date',        type: 'date' },
  { key: 'due_date',         label: 'Due',         type: 'date' },
  { key: 'grand_total',      label: 'Total',       type: 'currency', align: 'right' },
  { key: 'outstanding_amount', label: 'Outstanding', type: 'currency', align: 'right' },
  { key: 'status',           label: 'Status',      type: 'status' },
]

// Create-From: a Sales Invoice can be raised from either a submitted Quotation
// or a submitted Sales Order via whitelisted ERPNext mappers. Each mapped,
// unsaved invoice seeds FinanceForm for review + save.
const createFrom = [
  {
    key: 'from-quote',
    label: 'Create from Quote',
    sourceDoctype: 'Quotation',
    sourceLabel: 'Quotation',
    subtitleField: 'party_name',
    mapMethod: 'erpnext.selling.doctype.quotation.quotation.make_sales_invoice',
    targetDoctype: 'Sales Invoice',
  },
  {
    key: 'from-order',
    label: 'Create from Order',
    sourceDoctype: 'Sales Order',
    sourceLabel: 'Sales Order',
    subtitleField: 'customer',
    mapMethod: 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice',
    targetDoctype: 'Sales Invoice',
  },
]

function listParams() {
  const filters = []
  if (statusFilter.value === 'all') {
    // no filter
  } else if (statusFilter.value) {
    filters.push(['status', '=', statusFilter.value])
  } else {
    filters.push(['status', 'in', ['Unpaid', 'Partly Paid']])
  }
  return { company: company.value, filters: JSON.stringify(filters) }
}

function onFilterChange() {
  sectionRef.value?.resetPage()
  sectionRef.value?.refetch()
}
</script>
