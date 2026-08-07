<template>
  <div class="space-y-3">
    <div
      v-if="hrmsNotInstalled"
      class="flex flex-col items-center justify-center py-12 gap-3 text-gray-400 dark:text-gray-500"
    >
      <LucideAlertCircle class="w-10 h-10" />
      <p class="text-base font-semibold text-gray-600 dark:text-gray-300">HRMS Not Installed</p>
      <p class="text-sm">Expense Journals require the HRMS app.</p>
    </div>

    <FinanceTable
      v-else
      :columns="columns"
      :rows="journals"
      :loading="loading"
      :error="error"
      empty-label="No expense journals found."
      :page="page"
      :page-size="20"
      @update:page="p => { page = p; refetch() }"
      @retry="refetch"
    >
      <template #actions="{ row }">
        <a
          :href="'/app/journal-entry/' + row.name"
          target="_blank"
          class="text-xs px-2.5 py-1 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          @click.stop
        >View</a>
      </template>
    </FinanceTable>
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

const columns = [
  { key: 'name', label: 'Journal' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'entry_type', label: 'Type' },
  { key: 'total_debit', label: 'Amount', type: 'currency', align: 'right' },
  { key: 'remark', label: 'Remark' },
]

const resource = createResource({
  url: 'crm.finance.api.get_expense_journals',
  makeParams() {
    return {
      company: company.value,
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
const journals = computed(() => rawData.value.items || [])

function refetch() { resource.fetch() }
watch(company, () => { page.value = 0; resource.fetch() })
</script>
