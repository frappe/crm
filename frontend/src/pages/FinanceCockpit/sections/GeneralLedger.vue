<template>
  <div class="fc-general-ledger space-y-4">
    <div class="flex items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">General Ledger</h2>
    </div>

    <div class="flex gap-1 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        :class="[
          'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
          activeTab === tab.key
            ? 'border-blue-500 text-blue-600 dark:text-blue-400'
            : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300',
        ]"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- Journal Entries -->
    <div v-if="activeTab === 'journal'">
      <FinanceTable
        :columns="journalCols"
        :rows="journalRows"
        :loading="journalLoading"
        :error="journalError"
        empty-label="No journal entries found."
        :page="journalPage"
        :page-size="20"
        @update:page="p => { journalPage = p; journalRes.fetch() }"
        @retry="journalRes.fetch()"
      />
    </div>

    <!-- GL Entries viewer -->
    <div v-else-if="activeTab === 'gl'">
      <div class="flex flex-wrap gap-2 mb-3">
        <input
          v-model="glAccount"
          placeholder="Account"
          class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 w-40"
          @change="glPage = 0; glRes.fetch()"
        />
        <input
          v-model="glParty"
          placeholder="Party"
          class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 w-40"
          @change="glPage = 0; glRes.fetch()"
        />
        <input
          v-model="glFrom"
          type="date"
          class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          @change="glPage = 0; glRes.fetch()"
        />
        <input
          v-model="glTo"
          type="date"
          class="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
          @change="glPage = 0; glRes.fetch()"
        />
        <button
          class="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          @click="glPage = 0; glRes.fetch()"
        >Filter</button>
        <button
          class="text-xs px-3 py-1.5 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="exportCsv"
        >Export CSV</button>
      </div>
      <FinanceTable
        :columns="glCols"
        :rows="glRows"
        :loading="glLoading"
        :error="glError"
        empty-label="No GL entries found."
        :page="glPage"
        :page-size="50"
        @update:page="p => { glPage = p; glRes.fetch() }"
        @retry="glRes.fetch()"
      />
    </div>

    <!-- Period Closing -->
    <div v-else-if="activeTab === 'closing'">
      <div class="flex justify-end mb-3">
        <a
          href="/app/period-closing-voucher/new-period-closing-voucher-1"
          target="_blank"
          class="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >Create Period Closing</a>
      </div>
      <FinanceTable
        :columns="closingCols"
        :rows="closingRows"
        :loading="closingLoading"
        :error="closingError"
        empty-label="No period closing vouchers found."
        :page="closingPage"
        :page-size="20"
        @update:page="p => { closingPage = p; closingRes.fetch() }"
        @retry="closingRes.fetch()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceTable from '../components/FinanceTable.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const { company } = useCompanyContext()
const activeTab = ref('journal')

const TABS = [
  { key: 'journal', label: 'Journal Entries' },
  { key: 'gl', label: 'GL Entries' },
  { key: 'closing', label: 'Period Closing' },
]

// --- Journal Entries ---
const journalPage = ref(0)
const journalCols = [
  { key: 'name', label: 'Entry' },
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'entry_type', label: 'Type' },
  { key: 'total_debit', label: 'Total Debit', type: 'currency', align: 'right' },
  { key: 'remark', label: 'Remark' },
]
const journalRes = createResource({
  url: 'crm.finance.api.get_journal_entries',
  makeParams() { return { company: company.value, page: journalPage.value, page_size: 20 } },
  auto: true,
})
const journalRows = computed(() => journalRes.data || [])
const journalLoading = computed(() => journalRes.loading)
const journalError = computed(() => journalRes.error)

// --- GL Entries ---
const glPage = ref(0)
const glAccount = ref('')
const glParty = ref('')
const glFrom = ref('')
const glTo = ref('')
const glCols = [
  { key: 'posting_date', label: 'Date', type: 'date' },
  { key: 'account', label: 'Account' },
  { key: 'voucher_type', label: 'Voucher Type' },
  { key: 'voucher_no', label: 'Voucher No' },
  { key: 'party', label: 'Party' },
  { key: 'debit', label: 'Debit', type: 'currency', align: 'right' },
  { key: 'credit', label: 'Credit', type: 'currency', align: 'right' },
]
const glRes = createResource({
  url: 'crm.finance.api.get_gl_entries',
  makeParams() {
    const filters = []
    if (glAccount.value) filters.push(['account', 'like', '%' + glAccount.value + '%'])
    if (glParty.value) filters.push(['party', 'like', '%' + glParty.value + '%'])
    if (glFrom.value) filters.push(['posting_date', '>=', glFrom.value])
    if (glTo.value) filters.push(['posting_date', '<=', glTo.value])
    return { company: company.value, filters: JSON.stringify(filters), page: glPage.value, page_size: 50 }
  },
  auto: false,
})
const glRows = computed(() => glRes.data || [])
const glLoading = computed(() => glRes.loading)
const glError = computed(() => glRes.error)

// Watch tab change to trigger GL fetch
watch(activeTab, (t) => {
  if (t === 'gl' && !glRes.data) glRes.fetch()
  if (t === 'closing' && !closingRes.data) closingRes.fetch()
})

function exportCsv() {
  const rows = glRes.data || []
  if (!rows.length) return
  const cols = glCols.map(c => c.key)
  const header = glCols.map(c => c.label).join(',')
  const lines = rows.map(r => cols.map(k => JSON.stringify(r[k] ?? '')).join(','))
  const blob = new Blob([header + '\n' + lines.join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'gl_entries.csv'
  a.click()
}

// --- Period Closing ---
const closingPage = ref(0)
const closingCols = [
  { key: 'name', label: 'Voucher' },
  { key: 'transaction_date', label: 'Date', type: 'date' },
  { key: 'fiscal_year', label: 'Fiscal Year' },
  { key: 'closing_account_head', label: 'Closing Account' },
]
const closingRes = createResource({
  url: 'crm.finance.api.get_period_closing_vouchers',
  makeParams() { return { company: company.value, page: closingPage.value, page_size: 20 } },
  auto: false,
})
const closingRows = computed(() => closingRes.data || [])
const closingLoading = computed(() => closingRes.loading)
const closingError = computed(() => closingRes.error)

watch(company, () => {
  journalPage.value = 0; journalRes.fetch()
  if (activeTab.value === 'gl') { glPage.value = 0; glRes.fetch() }
  if (activeTab.value === 'closing') { closingPage.value = 0; closingRes.fetch() }
})
</script>
