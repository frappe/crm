<template>
  <FinanceTable
    :columns="columns"
    :rows="payments"
    :loading="loading"
    :error="error"
    empty-label="No supplier payments found."
    :page="page"
    :page-size="20"
    @update:page="p => { page = p; refetch() }"
    @retry="refetch"
  />
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceTable from '../../components/FinanceTable.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const page = ref(0)

const columns = [
  { key: 'name', label: 'Payment' },
  { key: 'party', label: 'Supplier' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'paid_amount', label: 'Paid', type: 'currency', align: 'right' },
  { key: 'unallocated_amount', label: 'Unallocated', type: 'currency', align: 'right' },
  { key: 'mode_of_payment', label: 'Mode' },
]

const resource = createResource({
  url: 'crm.finance.api.get_supplier_payments',
  makeParams() {
    return { company: company.value, page: page.value, page_size: 20 }
  },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const payments = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
