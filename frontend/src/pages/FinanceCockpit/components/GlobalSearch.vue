<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-start justify-center pt-16"
  >
    <!-- backdrop -->
    <div class="absolute inset-0 bg-black/40" @click="close" />

    <!-- modal -->
    <div
      class="relative w-full max-w-2xl mx-4 bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      @keydown="onKeydown"
    >
      <!-- search input -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <LucideSearch class="w-5 h-5 text-gray-400 shrink-0" />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          placeholder="Search invoices, payments, customers…"
          class="flex-1 bg-transparent text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400 outline-none"
        />
        <kbd class="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded border border-gray-200 dark:border-gray-600">Esc</kbd>
      </div>

      <!-- results -->
      <div class="max-h-96 overflow-y-auto">
        <template v-if="searchResource.loading && query.length > 1">
          <div class="px-4 py-8 text-center text-sm text-gray-400">Searching…</div>
        </template>

        <template v-else-if="query.length > 1 && totalCount === 0 && !searchResource.loading">
          <div class="px-4 py-8 text-center text-sm text-gray-400">No results for "{{ query }}"</div>
        </template>

        <template v-else-if="query.length < 2">
          <div class="px-4 py-8 text-center text-sm text-gray-400">Type to search across invoices, payments, customers and reports…</div>
        </template>

        <template v-else>
          <!-- Navigate group -->
          <template v-if="navigateItems.length > 0">
            <div class="px-4 pt-3 pb-1 flex items-center gap-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-400">Navigate</span>
              <span class="text-xs text-gray-400">({{ navigateItems.length }})</span>
            </div>
            <button
              v-for="(item, i) in navigateItems"
              :key="item.key"
              :class="[
                'w-full text-left flex items-center gap-3 px-4 py-2 transition-colors text-sm',
                focusedIndex === i ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
              @click="selectItem(item)"
            >
              <span class="flex-1 truncate text-gray-900 dark:text-gray-100">{{ item.label }}</span>
              <span class="text-xs text-gray-400 shrink-0">{{ item.subtitle }}</span>
            </button>
          </template>

          <!-- Reports group -->
          <template v-if="reportItems.length > 0">
            <div class="px-4 pt-3 pb-1 flex items-center gap-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-yellow-600 dark:text-yellow-400">Reports</span>
              <span class="text-xs text-gray-400">({{ reportItems.length }})</span>
            </div>
            <button
              v-for="(item, i) in reportItems"
              :key="item.key"
              :class="[
                'w-full text-left flex items-center gap-3 px-4 py-2 transition-colors text-sm',
                focusedIndex === navigateItems.length + i ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
              @click="selectItem(item)"
            >
              <span class="flex-1 truncate text-gray-900 dark:text-gray-100">{{ item.label }}</span>
              <span class="text-xs text-gray-400 shrink-0">{{ item.subtitle }}</span>
            </button>
          </template>

          <!-- Records group -->
          <template v-if="recordItems.length > 0">
            <div class="px-4 pt-3 pb-1 flex items-center gap-2">
              <span class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Records</span>
              <span class="text-xs text-gray-400">({{ recordItems.length }})</span>
            </div>
            <button
              v-for="(item, i) in recordItems"
              :key="item.key"
              :class="[
                'w-full text-left flex items-center gap-3 px-4 py-2 transition-colors text-sm',
                focusedIndex === navigateItems.length + reportItems.length + i ? 'bg-blue-50 dark:bg-blue-900/30' : 'hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
              @click="selectItem(item)"
            >
              <span class="flex-1 truncate text-gray-900 dark:text-gray-100">{{ item.label }}</span>
              <span class="text-xs text-gray-400 shrink-0">{{ item.subtitle }}</span>
            </button>
          </template>
        </template>
      </div>

      <!-- footer hint -->
      <div class="flex items-center gap-4 px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-400">
        <span><kbd class="font-mono">↑↓</kbd> navigate</span>
        <span><kbd class="font-mono">↵</kbd> open</span>
        <span><kbd class="font-mono">Esc</kbd> close</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { createResource } from 'frappe-ui'
import LucideSearch from '~icons/lucide/search'
import { REPORTS } from '../constants/reportsConfig.js'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const props = defineProps({
  visible: Boolean,
  userRoles: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'navigate'])

const { company } = useCompanyContext()
const query = ref('')
const inputRef = ref(null)
const focusedIndex = ref(0)
let debounceTimer = null

function close() {
  emit('close')
  query.value = ''
  focusedIndex.value = 0
}

watch(() => props.visible, async (val) => {
  if (val) {
    await nextTick()
    inputRef.value?.focus()
    query.value = ''
    focusedIndex.value = 0
  }
})

// Debounced search via createResource
const debouncedQuery = ref('')
watch(query, (val) => {
  clearTimeout(debounceTimer)
  focusedIndex.value = 0
  if (val.length < 2) {
    debouncedQuery.value = ''
    return
  }
  debounceTimer = setTimeout(() => {
    debouncedQuery.value = val
    searchResource.fetch()
  }, 250)
})

const searchResource = createResource({
  url: 'crm.finance.api.global_search',
  makeParams() {
    return {
      query: debouncedQuery.value,
      company: company.value,
      limit: 20,
    }
  },
})

const apiData = computed(() => searchResource.data || { records: [], navigate: [], reports: [], create: [] })

// Report search (client-side)
const reportItems = computed(() => {
  if (!query.value || query.value.length < 2) return []
  const q = query.value.toLowerCase()
  return REPORTS
    .filter(r => {
      const hasRole = r.roles.some(role => props.userRoles.includes(role))
      return hasRole && r.label.toLowerCase().includes(q)
    })
    .slice(0, 5)
    .map(r => ({
      key: 'report-' + r.report,
      label: r.label,
      subtitle: r.group,
      type: 'report',
      url: buildReportUrl(r),
    }))
})

function buildReportUrl(r) {
  const base = '/app/query-report/' + encodeURIComponent(r.report)
  const params = {}
  for (const [k, v] of Object.entries(r.defaultFilters || {})) {
    params[k] = v === '__COMPANY__' ? (company.value || '') : v
  }
  const qs = new URLSearchParams(params).toString()
  return qs ? base + '?' + qs : base
}

const navigateItems = computed(() =>
  (apiData.value.navigate || []).map(i => ({
    ...i,
    key: 'nav-' + (i.label || i.key || i.name),
    type: 'navigate',
  }))
)

const recordItems = computed(() =>
  (apiData.value.records || []).map(i => ({
    ...i,
    key: 'rec-' + i.doctype + '-' + i.name,
    type: 'record',
  }))
)

const allItems = computed(() => [
  ...navigateItems.value,
  ...reportItems.value,
  ...recordItems.value,
])

const totalCount = computed(() => allItems.value.length)

function onKeydown(e) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    focusedIndex.value = Math.min(focusedIndex.value + 1, totalCount.value - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    focusedIndex.value = Math.max(focusedIndex.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = allItems.value[focusedIndex.value]
    if (item) selectItem(item)
  } else if (e.key === 'Escape') {
    close()
  }
}

function selectItem(item) {
  if (item.type === 'navigate') {
    emit('navigate', item.section || item.key)
  } else if (item.url) {
    window.open(item.url, '_blank')
  }
  close()
}
</script>
