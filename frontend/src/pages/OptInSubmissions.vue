<template>
  <div class="flex h-full flex-col overflow-hidden">

    <!-- Header -->
    <div class="flex items-center justify-between border-b border-outline-gray-2 px-5 py-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Opt-In Requests') }}</h1>
    </div>

    <!-- Status filter chips -->
    <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2 px-5 py-2.5">
      <button
        v-for="s in statuses"
        :key="s"
        :class="[
          'rounded-full px-3 py-1 text-xs font-medium transition-colors',
          selectedStatus === s
            ? 'bg-red-600 text-white'
            : 'bg-surface-gray-2 text-ink-gray-6 hover:bg-surface-gray-3 dark:bg-surface-gray-4 dark:text-ink-gray-4 dark:hover:bg-surface-gray-5',
        ]"
        @click="setStatus(s)"
      >{{ __(s) }}</button>
    </div>

    <!-- Table -->
    <div class="flex-1 overflow-auto">
      <div v-if="listResource.loading" class="flex items-center justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent" />
      </div>

      <div v-else-if="!rows.length" class="flex flex-col items-center justify-center py-16 text-center">
        <p class="text-sm font-medium text-ink-gray-5">{{ __('No submissions found') }}</p>
        <p class="mt-1 text-xs text-ink-gray-4">{{ __('Try adjusting your filters.') }}</p>
      </div>

      <table v-else class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-5 py-2.5 text-left font-medium">{{ __('Ref #') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Network') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Submitter') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Submitted') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Lead') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Deal') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="row in rows"
            :key="row.name"
            :class="[
              'transition-colors',
              row.deal ? 'cursor-pointer hover:bg-surface-gray-1' : 'cursor-default',
            ]"
            @click="openDeal(row)"
          >
            <td class="px-5 py-3 font-medium text-ink-gray-9">{{ row.name }}</td>
            <td class="px-4 py-3 text-ink-gray-7">{{ row.network_slug || '—' }}</td>
            <td class="px-4 py-3 text-ink-gray-6 text-xs">{{ row.submitter_email || '—' }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ formatDate(row.submitted_at) }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.lead || '—' }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.deal || '—' }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap items-center gap-1.5">
                <span :class="statusPill(row.status)">{{ __(row.status) }}</span>
                <span
                  v-if="row.has_duplicate_mfl"
                  class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                >{{ __('Duplicate MFL') }}</span>
              </div>
            </td>
            <td class="px-4 py-3" @click.stop>
              <Button
                v-if="row.status === 'Failed'"
                size="sm"
                variant="subtle"
                :loading="retrying === row.name"
                @click="retry(row)"
              >{{ __('Retry') }}</Button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex items-center justify-between border-t border-outline-gray-2 px-5 py-3">
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
import { createResource, Button } from 'frappe-ui'
import { useRouter } from 'vue-router'

const router = useRouter()

const statuses = ['All', 'Pending', 'Processing', 'Processed', 'Failed']
const selectedStatus = ref('All')
const page = ref(0)
const pageSize = 20
const retrying = ref(null)

function setStatus(s) {
  selectedStatus.value = s
  page.value = 0
}

watch(page, () => listResource.reload())

const listResource = createResource({
  url: 'crm.api.optin.list_submissions',
  makeParams: () => ({
    status: selectedStatus.value === 'All' ? null : selectedStatus.value,
    page: page.value,
    page_size: pageSize,
  }),
  auto: true,
})

watch(selectedStatus, () => listResource.reload())

const rows = computed(() => listResource.data?.rows ?? [])
const total = computed(() => listResource.data?.total ?? 0)

const retryResource = createResource({ url: 'crm.api.optin.retry_submission' })

async function retry(row) {
  retrying.value = row.name
  try {
    await retryResource.submit({ submission_ref: row.name })
    listResource.reload()
  } finally {
    retrying.value = null
  }
}

function openDeal(row) {
  if (!row.deal) return
  router.push({ name: 'Deal', params: { dealId: row.deal } })
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function statusPill(status) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    Pending:    `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`,
    Processing: `${base} bg-surface-gray-3 text-ink-gray-8 dark:bg-surface-gray-5 dark:text-ink-gray-3`,
    Processed:  `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`,
    Failed:     `${base} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`,
  }
  return map[status] ?? map.Pending
}
</script>
