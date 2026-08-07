<template>
  <FinanceTable
    :columns="columns"
    :rows="orders"
    :loading="loading"
    :error="error"
    empty-label="No purchase orders found."
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
  { key: 'name', label: 'Order' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'transaction_date', label: 'Date', type: 'date' },
  { key: 'grand_total', label: 'Total', type: 'currency', align: 'right' },
  { key: 'status', label: 'Status', type: 'status' },
  { key: 'billing_status', label: 'Billing', type: 'status' },
]

const resource = createResource({
  url: 'crm.finance.api.get_purchase_orders',
  makeParams() {
    return { company: company.value, page: page.value, page_size: 20 }
  },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const orders = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
