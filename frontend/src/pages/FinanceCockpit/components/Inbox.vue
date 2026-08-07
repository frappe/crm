<template>
  <div class="fc-inbox space-y-4">
    <!-- Header + filter pills -->
    <div class="flex flex-wrap items-center gap-2">
      <h2 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide flex-1">
        Inbox
        <span
          v-if="totalCount > 0"
          class="ml-2 text-xs bg-red-500 text-white rounded-full px-1.5 py-0.5"
        >{{ totalCount }}</span>
      </h2>
      <button
        class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 transition-colors"
        :disabled="loading"
        @click="refetch"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
      </button>
    </div>

    <!-- Filter pills -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="pill in FILTER_PILLS"
        :key="pill.key"
        :class="[
          'px-3 py-1 rounded-full text-xs font-medium transition-colors border',
          activeFilter === pill.key
            ? 'bg-blue-600 text-white border-blue-600'
            : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-blue-400',
        ]"
        @click="activeFilter = pill.key"
      >{{ pill.label }}</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 4" :key="n" class="h-16 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-sm text-red-500 py-2">
      Failed to load inbox. <button class="underline" @click="refetch">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!filteredItems.length" class="text-center py-10 text-sm text-gray-400">
      <svg class="mx-auto mb-2 text-gray-300 dark:text-gray-600" xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
      All clear — no pending actions.
    </div>

    <!-- Urgency bands -->
    <template v-else>
      <InboxUrgencyBand
        v-for="band in ['critical', 'warning', 'normal']"
        :key="band"
        :urgency="band"
        :items="bandItems(band)"
      >
        <InboxItem
          v-for="item in bandItems(band)"
          :key="item.docname + item.type"
          :item="item"
        />
      </InboxUrgencyBand>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useCompanyContext } from '../composables/useCompanyContext.js'
import InboxUrgencyBand from './InboxUrgencyBand.vue'
import InboxItem from './InboxItem.vue'

const { company } = useCompanyContext()

const FILTER_PILLS = [
  { key: 'all', label: 'All' },
  { key: 'receivables', label: 'Receivables' },
  { key: 'payables', label: 'Payables' },
  { key: 'expenses', label: 'Expenses' },
  { key: 'banking', label: 'Banking' },
  { key: 'partner', label: 'Partner' },
]

const TYPE_FILTER_MAP = {
  receivables: ['overdue_invoice', 'unapplied_payment', 'unconfirmed_commission', 'subscription_invoice_due'],
  payables: ['overdue_purchase_invoice', 'purchase_invoice_pending_approval'],
  expenses: ['expense_claim_pending_payment', 'employee_advance_unclaimed'],
  banking: ['bank_transaction_unmatched'],
  partner: ['pending_rebate', 'approved_rebate_unpaid', 'confirmed_commission_unpaid'],
}

const activeFilter = ref('all')

const inboxResource = createResource({
  url: 'crm.finance.api.get_pending_actions',
  makeParams() {
    return { company: company.value }
  },
  auto: true,
})

const loading = computed(() => inboxResource.loading)
const error = computed(() => inboxResource.error)

const allItems = computed(() => inboxResource.data || [])
const totalCount = computed(() => allItems.value.length)

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return allItems.value
  const types = TYPE_FILTER_MAP[activeFilter.value] || []
  return allItems.value.filter(i => types.includes(i.type))
})

function bandItems(urgency) {
  return filteredItems.value.filter(i => i.urgency === urgency)
}

function refetch() {
  inboxResource.fetch()
}

watch(company, () => { inboxResource.fetch() })

// Expose badge count for sidebar
defineExpose({ totalCount })
</script>
