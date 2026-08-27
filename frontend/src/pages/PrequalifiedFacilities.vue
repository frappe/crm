<template>
  <div class="flex h-full flex-col overflow-hidden">

    <!-- Header -->
    <div class="border-b border-outline-gray-2 px-5 pt-3 pb-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('All Prequalified Contacts') }}</h1>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-wrap items-center gap-3 border-b border-outline-gray-2 px-5 py-2.5">
      <select
        v-model="filterNetwork"
        class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-7 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-2 dark:text-ink-gray-4"
        @change="onFilterChange"
      >
        <option value="">{{ __('All Networks') }}</option>
        <option v-for="n in networkRows" :key="n.name" :value="n.slug">{{ n.display_name }}</option>
      </select>

      <button
        v-for="s in facilityStatuses"
        :key="s"
        :class="[
          'rounded-full px-3 py-1 text-xs font-medium transition-colors',
          filterStatus === s
            ? 'bg-red-600 text-white'
            : 'bg-surface-gray-2 text-ink-gray-6 hover:bg-surface-gray-3 dark:bg-surface-gray-4 dark:text-ink-gray-4 dark:hover:bg-surface-gray-5',
        ]"
        @click="setFacilityStatus(s)"
      >{{ __(s) }}</button>
    </div>

    <!-- Table -->
    <div class="flex-1 overflow-auto">
      <div v-if="facilityListResource.loading" class="flex items-center justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent" />
      </div>

      <div v-else-if="!facilityRows.length" class="flex flex-col items-center justify-center py-16 text-center">
        <p class="text-sm font-medium text-ink-gray-5">{{ __('No facilities found') }}</p>
        <p class="mt-1 text-xs text-ink-gray-4">{{ __('Adjust filters or add contacts via a network detail page.') }}</p>
      </div>

      <table v-else class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-5 py-2.5 text-left font-medium">{{ __('MFL Code') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Facility Name') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('KEPH Level') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Networks') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Contact Email') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="row in facilityRows"
            :key="row.name"
            class="transition-colors hover:bg-surface-gray-1"
          >
            <td class="px-5 py-3 font-mono text-xs font-medium text-ink-gray-9">{{ row.mfl_code }}</td>
            <td class="px-4 py-3 text-ink-gray-7">{{ row.facility_name }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.keph_level || '—' }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <button
                  v-for="m in (row.memberships ?? [])"
                  :key="m.network"
                  :class="membershipPill(m.status)"
                  @click="openNetworkDetail(m.network)"
                >{{ m.network }} →</button>
                <span v-if="!(row.memberships ?? []).length" class="text-xs text-ink-gray-4">—</span>
              </div>
            </td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ (row.memberships ?? [])[0]?.contact_email || '—' }}</td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="facilityTotal > facilityPageSize" class="flex items-center justify-between border-t border-outline-gray-2 px-5 py-3">
        <span class="text-xs text-ink-gray-5">
          {{ __('Showing {0}–{1} of {2}', [page * facilityPageSize + 1, Math.min((page + 1) * facilityPageSize, facilityTotal), facilityTotal]) }}
        </span>
        <div class="flex gap-2">
          <Button size="sm" variant="subtle" :disabled="page === 0" @click="prevPage">{{ __('Prev') }}</Button>
          <Button size="sm" variant="subtle" :disabled="(page + 1) * facilityPageSize >= facilityTotal" @click="nextPage">{{ __('Next') }}</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Button } from 'frappe-ui'

const router = useRouter()

// ── Networks for filter dropdown ───────────────────────────────────────────

const networksResource = createResource({
  url: 'crm.api.optin_admin.list_networks',
  makeParams: () => ({ page: 0, page_size: 200 }),
  auto: true,
})
const networkRows = computed(() => networksResource.data?.rows ?? [])

// ── Facilities list ────────────────────────────────────────────────────────

const facilityStatuses = ['All', 'Active', 'Opted In', 'Declined']
const filterStatus = ref('All')
const filterNetwork = ref('')
const page = ref(0)
const facilityPageSize = 20

const facilityListResource = createResource({
  url: 'crm.api.optin_admin.list_facilities',
  makeParams: () => ({
    network: filterNetwork.value || null,
    status: filterStatus.value === 'All' ? null : filterStatus.value,
    page: page.value,
    page_size: facilityPageSize,
  }),
  auto: true,
})

const facilityRows = computed(() => facilityListResource.data?.rows ?? [])
const facilityTotal = computed(() => facilityListResource.data?.total ?? 0)

function onFilterChange() {
  page.value = 0
  facilityListResource.reload()
}

function setFacilityStatus(s) {
  filterStatus.value = s
  page.value = 0
  facilityListResource.reload()
}

function prevPage() {
  page.value--
  facilityListResource.reload()
}

function nextPage() {
  page.value++
  facilityListResource.reload()
}

function openNetworkDetail(networkSlug) {
  router.push({ name: 'NetworkDetail', params: { networkSlug } })
}

function membershipPill(status) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium transition-colors hover:opacity-80 cursor-pointer'
  const map = {
    'Active':   `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`,
    'Opted In': `${base} bg-surface-gray-3 text-ink-gray-8 dark:bg-surface-gray-5 dark:text-ink-gray-3`,
    'Declined': `${base} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`,
  }
  return map[status] ?? `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`
}
</script>
