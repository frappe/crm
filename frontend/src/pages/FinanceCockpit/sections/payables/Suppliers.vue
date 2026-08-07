<template>
  <FinanceTable
    :columns="columns"
    :rows="suppliers"
    :loading="loading"
    :error="error"
    empty-label="No suppliers found."
    :page="page"
    :page-size="20"
    @update:page="p => { page = p; refetch() }"
    @retry="refetch"
  >
    <template #actions="{ row }">
      <a
        :href="'/app/query-report/Accounts Payable?supplier=' + encodeURIComponent(row.name)"
        target="_blank"
        class="text-xs px-2.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors whitespace-nowrap"
        @click.stop
      >View Statement</a>
    </template>
  </FinanceTable>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceTable from '../../components/FinanceTable.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const page = ref(0)

const columns = [
  { key: 'name', label: 'Supplier ID' },
  { key: 'supplier_name', label: 'Name' },
  { key: 'supplier_group', label: 'Group' },
  { key: 'supplier_type', label: 'Type' },
]

const resource = createResource({
  url: 'crm.finance.api.get_suppliers',
  makeParams() {
    return { company: company.value, page: page.value, page_size: 20 }
  },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const suppliers = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
