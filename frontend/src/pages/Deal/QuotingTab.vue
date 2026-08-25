<template>
  <div class="flex flex-col h-full overflow-y-auto px-3 pb-3 sm:px-10 sm:pb-5">

    <!-- Finance Cockpit handoff banner -->
    <div
      v-if="acceptedQuote"
      class="mt-4 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 dark:border-green-800 dark:bg-green-900/20"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0 text-green-600 dark:text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      <span class="text-sm text-green-800 dark:text-green-300">
        Quote accepted —
        <strong>{{ acceptedQuote.erpnext_sales_invoice }}</strong>
        created.
        <a
          href="/finance-cockpit#/receivables/invoices"
          target="_blank"
          class="ml-1 underline font-medium"
        >View in Finance Cockpit → Receivables → AR Invoices</a>
      </span>
    </div>

    <!-- Header row -->
    <div class="mt-4 flex items-center justify-between">
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Quotes') }}</h2>
      <Button variant="solid" @click="openBuilder(null)">
        <template #prefix>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </template>
        {{ __('New Quote') }}
      </Button>
    </div>

    <!-- Loading -->
    <div v-if="quotesResource.loading" class="mt-6 space-y-2">
      <div v-for="n in 2" :key="n" class="h-12 animate-pulse rounded-lg bg-surface-gray-2" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!quotes.length"
      class="mt-16 flex flex-col items-center gap-3 text-center"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-ink-gray-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <p class="text-sm font-medium text-ink-gray-5">{{ __('No quotes yet') }}</p>
      <p class="text-xs text-ink-gray-4">{{ __('Create a quote to send a formal proposal to this customer.') }}</p>
      <Button class="mt-2" variant="solid" @click="openBuilder(null)">
        {{ __('+ Create Quote') }}
      </Button>
    </div>

    <!-- Quote list table -->
    <div v-else class="mt-4 overflow-x-auto rounded-lg border border-outline-elevation-2">
      <table class="w-full text-sm">
        <thead class="bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Quote #') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Created') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Valid Until') }}</th>
            <th class="px-4 py-2.5 text-right font-medium">{{ __('Grand Total') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Payment') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-4 py-2.5 text-right font-medium">{{ __('Actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="q in quotes"
            :key="q.name"
            class="hover:bg-surface-gray-1 transition-colors"
          >
            <td class="px-4 py-3 font-medium text-ink-gray-9">{{ q.name }}</td>
            <td class="px-4 py-3">
              <span class="text-ink-gray-8 font-medium">{{ timeAgo(q.creation || q.quote_date) }}</span>
              <div class="text-xs text-ink-gray-4">{{ formatDate(q.quote_date) }}</div>
            </td>
            <td class="px-4 py-3" :class="isExpired(q) ? 'text-red-500 font-medium' : 'text-ink-gray-6'">
              {{ formatDate(q.valid_until) }}
            </td>
            <td class="px-4 py-3 text-right font-semibold text-ink-gray-9">{{ fmtKes(q.grand_total) }}</td>
            <td class="px-4 py-3 text-ink-gray-6 text-xs">{{ q.payment_terms }}</td>
            <td class="px-4 py-3">
              <span :class="pillClass(q)">
                {{ isExpired(q) ? __('Expired') : __(q.status) }}
              </span>
            </td>
            <td class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1.5">
                <Button size="sm" variant="ghost" @click="openBuilder(q.name)">{{ __('View') }}</Button>
                <Button
                  v-if="q.status === 'Draft' || q.status === 'Sent'"
                  size="sm" variant="ghost"
                  @click="sendQuote(q.name)"
                  :loading="sendingName === q.name"
                >{{ __('Send') }}</Button>
                <Button
                  v-if="q.status === 'Sent'"
                  size="sm" variant="ghost"
                  theme="green"
                  @click="acceptQuote(q.name)"
                  :loading="actionName === q.name"
                >{{ __('Accept') }}</Button>
                <Button
                  v-if="q.status === 'Sent'"
                  size="sm" variant="ghost"
                  theme="red"
                  @click="confirmReject(q.name)"
                >{{ __('Reject') }}</Button>
                <Button size="sm" variant="ghost" @click="downloadPdf(q.name)">{{ __('PDF') }}</Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Reject confirmation dialog -->
    <Dialog
      v-model="showRejectDialog"
      :options="{ title: __('Reject this quote?'), size: 'sm' }"
    >
      <template #body-content>
        <p class="text-sm text-ink-gray-6">
          {{ __('This will set the quote status to Rejected. A new version will be needed.') }}
        </p>
      </template>
      <template #actions>
        <Button variant="subtle" @click="showRejectDialog = false">{{ __('Cancel') }}</Button>
        <Button variant="solid" theme="red" :loading="actionName !== null" @click="doReject">
          {{ __('Confirm Reject') }}
        </Button>
      </template>
    </Dialog>

    <!-- Quote builder overlay (lazy-loaded) -->
    <QuoteBuilder
      v-if="builderOpen"
      :deal-id="dealId"
      :quote-name="builderQuoteName"
      @close="onBuilderClose"
      @saved="onBuilderClose(true)"
    />
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'
import { createResource } from 'frappe-ui'
import { Button, Dialog } from 'frappe-ui'

const QuoteBuilder = defineAsyncComponent(() =>
  import('./QuoteBuilder.vue')
)

const props = defineProps({
  dealId: { type: String, required: true },
})

const quotesResource = createResource({
  url: 'crm.api.quotes.list_quotes',
  makeParams: () => ({ deal: props.dealId }),
  auto: true,
})

const quotes = computed(() => quotesResource.data || [])

const acceptedQuote = computed(() =>
  quotes.value.find(q => q.status === 'Accepted' && q.erpnext_sales_invoice)
)

// Builder state
const builderOpen = ref(false)
const builderQuoteName = ref(null)

function openBuilder(quoteName) {
  builderQuoteName.value = quoteName
  builderOpen.value = true
}

function onBuilderClose(shouldReload = false) {
  builderOpen.value = false
  builderQuoteName.value = null
  if (shouldReload) quotesResource.reload()
}

// Actions
const sendingName = ref(null)
const actionName = ref(null)

const sendResource = createResource({ url: 'crm.api.quotes.send_quote' })
const acceptResource = createResource({ url: 'crm.api.quotes.accept_quote' })
const rejectResource = createResource({ url: 'crm.api.quotes.reject_quote' })

async function sendQuote(name) {
  sendingName.value = name
  try {
    await sendResource.submit({ quote_name: name })
    quotesResource.reload()
  } finally {
    sendingName.value = null
  }
}

async function acceptQuote(name) {
  actionName.value = name
  try {
    await acceptResource.submit({ quote_name: name })
    quotesResource.reload()
  } finally {
    actionName.value = null
  }
}

// Reject dialog
const showRejectDialog = ref(false)
const rejectTargetName = ref(null)

function confirmReject(name) {
  rejectTargetName.value = name
  showRejectDialog.value = true
}

async function doReject() {
  actionName.value = rejectTargetName.value
  try {
    await rejectResource.submit({ quote_name: rejectTargetName.value })
    quotesResource.reload()
    showRejectDialog.value = false
  } finally {
    actionName.value = null
    rejectTargetName.value = null
  }
}

function downloadPdf(name) {
  window.open(
    `/api/method/frappe.utils.print_format.download_pdf?doctype=Quotation&name=${encodeURIComponent(name)}&format=Careverse+Quote+Standard`,
    '_blank'
  )
}

// Helpers
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function fmtKes(v) {
  if (!v && v !== 0) return '—'
  const n = parseFloat(v)
  if (n >= 1_000_000) return 'KES ' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return 'KES ' + (n / 1_000).toFixed(1) + 'K'
  return 'KES ' + n.toLocaleString()
}

function isExpired(q) {
  if (!q.valid_until || q.status === 'Accepted' || q.status === 'Rejected') return false
  return new Date(q.valid_until) < new Date()
}

function pillClass(q) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  if (isExpired(q)) return `${base} bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400`
  const map = {
    Draft:    `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`,
    Sent:     `${base} bg-surface-gray-3 text-ink-gray-8 dark:bg-surface-gray-5 dark:text-ink-gray-3`,
    Accepted: `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`,
    Rejected: `${base} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`,
  }
  return map[q.status] || map.Draft
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60)  return __('just now')
  if (diff < 3600) return Math.floor(diff / 60) + ' ' + __('min ago')
  if (diff < 86400) return Math.floor(diff / 3600) + ' ' + __('hr ago')
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + ' ' + __('d ago')
  return formatDate(dateStr)
}
</script>
