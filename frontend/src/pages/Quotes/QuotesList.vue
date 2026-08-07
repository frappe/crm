<template>
  <div class="flex h-full flex-col overflow-hidden">

    <!-- Page header -->
    <div class="flex items-center justify-between border-b border-outline-elevation-2 px-5 py-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Quotes') }}</h1>
    </div>

    <!-- KPI bar -->
    <div class="grid grid-cols-2 gap-3 border-b border-outline-elevation-2 px-5 py-3 sm:grid-cols-4">
      <div
        v-for="kpi in kpiTiles"
        :key="kpi.key"
        class="rounded-lg border border-outline-elevation-2 bg-surface-white px-4 py-3"
      >
        <p class="text-xs font-medium uppercase tracking-wide text-ink-gray-4">{{ __(kpi.label) }}</p>
        <p class="mt-1 text-xl font-bold text-ink-gray-9">{{ kpi.value }}</p>
      </div>
    </div>

    <!-- Filters row -->
    <div class="flex flex-wrap items-center gap-2 border-b border-outline-elevation-2 px-5 py-2.5">
      <!-- Status pills -->
      <button
        v-for="s in statuses"
        :key="s"
        :class="[
          'rounded-full px-3 py-1 text-xs font-medium transition-colors',
          selectedStatus === s
            ? 'bg-blue-600 text-white'
            : 'bg-surface-gray-2 text-ink-gray-6 hover:bg-surface-gray-3',
        ]"
        @click="selectedStatus = s"
      >{{ __(s) }}</button>

      <div class="ml-auto flex items-center gap-2">
        <!-- Search -->
        <input
          v-model="search"
          type="text"
          :placeholder="__('Search quotes...')"
          class="rounded-md border border-outline-elevation-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:border-blue-500 focus:outline-none dark:bg-surface-gray-1"
        />
        <!-- Export CSV -->
        <Button size="sm" variant="subtle" @click="exportCsv">{{ __('Export CSV') }}</Button>
      </div>
    </div>

    <!-- Table -->
    <div class="flex-1 overflow-auto">
      <div v-if="listResource.loading" class="flex items-center justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>

      <div v-else-if="!rows.length" class="flex flex-col items-center justify-center py-16 text-center">
        <p class="text-sm font-medium text-ink-gray-5">{{ __('No quotes found') }}</p>
        <p class="mt-1 text-xs text-ink-gray-4">{{ __('Try adjusting your filters.') }}</p>
      </div>

      <table v-else class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-5 py-2.5 text-left font-medium">{{ __('Quote #') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Customer') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Deal') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Rep') }}</th>
            <th class="px-4 py-2.5 text-right font-medium">{{ __('Grand Total') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Valid Until') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="row in rows"
            :key="row.name"
            class="cursor-pointer hover:bg-surface-gray-1 transition-colors"
            @click="openDeal(row)"
          >
            <td class="px-5 py-3 font-medium text-blue-600">{{ row.name }}</td>
            <td class="px-4 py-3 text-ink-gray-7">{{ row.customer || '—' }}</td>
            <td class="px-4 py-3 text-ink-gray-6 text-xs">{{ row.deal }}</td>
            <td class="px-4 py-3 text-ink-gray-6 text-xs">{{ row.owner }}</td>
            <td class="px-4 py-3 text-right font-semibold text-ink-gray-9">{{ fmtKes(row.grand_total) }}</td>
            <td class="px-4 py-3">
              <span :class="pillClass(row)">
                {{ isExpired(row) ? __('Expired') : __(row.status) }}
              </span>
            </td>
            <td
              class="px-4 py-3 text-xs"
              :class="isExpired(row) ? 'font-medium text-red-500' : 'text-ink-gray-6'"
            >{{ formatDate(row.valid_until) }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex items-center justify-between border-t border-outline-elevation-2 px-5 py-3">
        <span class="text-xs text-ink-gray-5">
          {{ __('Showing {0}–{1} of {2}', [page * pageSize + 1, Math.min((page + 1) * pageSize, total), total]) }}
        </span>
        <div class="flex gap-2">
          <Button size="sm" variant="subtle" :disabled="page === 0" @click="page--">{{ __('Prev') }}</Button>
          <Button size="sm" variant="subtle" :disabled="(page + 1) * pageSize >= total" @click="page++">{{ __('Next') }}</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { Button } from 'frappe-ui'
import { useRouter } from 'vue-router'

const router = useRouter()

const statuses = ['All', 'Draft', 'Sent', 'Accepted', 'Rejected', 'Expired']
const selectedStatus = ref('All')
const search = ref('')
const page = ref(0)
const pageSize = 20

// Reset to page 0 on filter change
watch([selectedStatus, search], () => { page.value = 0 })

const listResource = createResource({
  url: 'crm.api.quotes.list_all_quotes',
  makeParams: () => ({
    status: selectedStatus.value,
    search: search.value || null,
    page: page.value,
    page_size: pageSize,
  }),
  auto: true,
})

watch([selectedStatus, search, page], () => listResource.reload())

const rows = computed(() => listResource.data?.rows || [])
const total = computed(() => listResource.data?.total || 0)
const kpis = computed(() => listResource.data?.kpis || {})

const kpiTiles = computed(() => [
  { key: 'draft',     label: 'Draft',               value: kpis.value.draft_count ?? 0 },
  { key: 'sent',      label: 'Sent (Pending)',        value: kpis.value.sent_count ?? 0 },
  { key: 'accepted',  label: 'Accepted This Month',   value: fmtKes(kpis.value.accepted_this_month) },
  { key: 'pipeline',  label: 'Pipeline Value',        value: fmtKes(kpis.value.pipeline_value) },
])

function openDeal(row) {
  router.push({ name: 'Deal', params: { dealId: row.deal }, query: { tab: 'quoting', quote: row.name } })
}

function exportCsv() {
  const exportResource = createResource({
    url: 'crm.api.quotes.list_all_quotes',
    makeParams: () => ({
      status: selectedStatus.value,
      search: search.value || null,
      page: 0,
      page_size: 9999,
    }),
  })
  exportResource.fetch().then(() => {
    const data = exportResource.data?.rows || []
    if (!data.length) return
    const headers = Object.keys(data[0])
    const csv = [headers.join(','), ...data.map(r => headers.map(h => JSON.stringify(r[h] ?? '')).join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'quotes.csv'
    a.click()
    URL.revokeObjectURL(url)
  })
}

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

function isExpired(row) {
  if (!row.valid_until || row.status === 'Accepted' || row.status === 'Rejected') return false
  return new Date(row.valid_until) < new Date()
}

function pillClass(row) {
  if (isExpired(row)) return 'rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  const map = {
    Draft:    'rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    Sent:     'rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    Accepted: 'rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400',
    Rejected: 'rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400',
  }
  return map[row.status] || map.Draft
}
</script>
