<template>
  <CrudSection
    ref="sectionRef"
    doctype="Sales Invoice"
    title="AR Invoices"
    :columns="columns"
    list-resource-url="crm.finance.api.get_ar_invoices"
    :list-params="listParams"
    empty-label="No invoices found."
  >
    <template #filters>
      <label class="text-xs text-gray-500 dark:text-gray-400">Status:</label>
      <select
        v-model="statusFilter"
        class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
        @change="onFilterChange"
      >
        <option value="">Unpaid + Partly Paid</option>
        <option value="all">All</option>
        <option value="Unpaid">Unpaid</option>
        <option value="Partly Paid">Partly Paid</option>
      </select>
    </template>
  </CrudSection>
</template>

<script setup>
import { ref, watch } from 'vue'
import CrudSection from '../../components/crud/CrudSection.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const statusFilter = ref('')
const sectionRef = ref(null)

const columns = [
  { key: 'name', label: 'Invoice' },
  { key: 'customer', label: 'Customer' },
  { key: 'posting_date', label: 'Date', type: 'timeago' },
  { key: 'due_date', label: 'Due', type: 'date' },
  { key: 'outstanding_amount', label: 'Outstanding', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
  { key: 'name', label: '', type: 'print-action', width: 0.4 },
]

function listParams() {
  const filters = []
  if (statusFilter.value && statusFilter.value !== 'all') {
    filters.push(['status', '=', statusFilter.value])
  } else if (!statusFilter.value) {
    filters.push(['status', 'in', ['Unpaid', 'Partly Paid']])
  }
  return {
    company: company.value,
    filters: JSON.stringify(filters),
  }
}

function onFilterChange() {
  sectionRef.value?.resetPage()
  sectionRef.value?.refetch()
}

// Reset + refetch when the active company changes.
watch(company, () => {
  sectionRef.value?.resetPage()
  sectionRef.value?.refetch()
})
</script>
