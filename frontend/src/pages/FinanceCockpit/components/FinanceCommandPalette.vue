<template>
  <!-- Fixed-position in-tree overlay — avoids reka-ui DialogPortal/Teleport which
       silently fails on standalone www pages (useMounted guard stays false). -->
  <Teleport to="body">
    <div
      v-if="localShow"
      class="fixed inset-0 z-50"
      @keydown.esc.stop="localShow = false"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/40 dark:bg-black/60 transition-opacity"
        @click="localShow = false"
      />

      <!-- Palette panel -->
      <div class="relative z-10 flex items-start justify-center pt-[14vh] px-4">
        <div
          class="w-full max-w-2xl bg-surface-white dark:bg-surface-gray-1 rounded-xl shadow-2xl border border-outline-gray-1 overflow-hidden"
          @click.stop
        >
          <Combobox nullable @update:model-value="onSelect">
            <!-- Search input -->
            <div class="relative border-b border-outline-gray-1">
              <span class="absolute inset-y-0 left-0 flex items-center pl-4">
                <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
              </span>
              <ComboboxInput
                ref="inputRef"
                v-model="query"
                autocomplete="off"
                placeholder="Search…"
                class="w-full bg-transparent py-3.5 pl-11 pr-4 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:outline-none"
              />
            </div>

            <ComboboxOptions
              class="max-h-96 overflow-y-auto py-2"
              static
              :hold="true"
            >
              <div v-if="!allItems.length" class="px-4 py-8 text-center text-sm text-ink-gray-4">
                Type to search…
              </div>
              <template v-for="group in groups" :key="group.title">
                <div class="px-4 pt-3 pb-1 text-xs font-semibold text-ink-gray-5 uppercase tracking-wide">
                  {{ group.title }}
                </div>
                <ComboboxOption
                  v-for="item in group.items"
                  :key="item.name"
                  :value="item"
                  v-slot="{ active }"
                  class="px-2"
                >
                  <div
                    class="flex items-center gap-3 rounded-lg px-3 py-2.5 cursor-pointer transition-colors"
                    :class="active ? 'bg-surface-gray-2 dark:bg-surface-gray-3' : ''"
                  >
                    <span
                      v-if="typeof item.icon === 'string'"
                      :class="[item.icon, 'size-4 text-ink-gray-5 flex-shrink-0']"
                      aria-hidden="true"
                    />
                    <component
                      v-else-if="item.icon"
                      :is="item.icon"
                      class="size-4 text-ink-gray-5 flex-shrink-0"
                    />
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-ink-gray-8 truncate">{{ item.title }}</p>
                      <p v-if="item.description" class="text-xs text-ink-gray-5 truncate">{{ item.description }}</p>
                    </div>
                  </div>
                </ComboboxOption>
              </template>
            </ComboboxOptions>
          </Combobox>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/vue'
import { createResource, useShortcut } from 'frappe-ui'
import LucideCompass from '~icons/lucide/compass'
import LucideBarChart2 from '~icons/lucide/bar-chart-2'
import LucideFileText from '~icons/lucide/file-text'
import { REPORTS } from '../constants/reportsConfig.js'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  userRoles: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:show', 'navigate'])

const { company } = useCompanyContext()

const localShow = ref(props.show)
const inputRef = ref(null)

watch(() => props.show, (v) => { localShow.value = v })
watch(localShow, (v) => {
  emit('update:show', v)
  if (v) nextTick(() => inputRef.value?.$el?.focus())
})

useShortcut({
  key: 'k',
  ctrl: true,
  description: 'Open command palette',
  group: 'Navigation',
  handler: () => { localShow.value = true },
})

const query = ref('')

const debouncedQuery = ref('')
let debounceTimer = null
watch(query, (val) => {
  clearTimeout(debounceTimer)
  if (!val || val.length < 2) { debouncedQuery.value = ''; return }
  debounceTimer = setTimeout(() => { debouncedQuery.value = val; searchResource.fetch() }, 250)
})

const searchResource = createResource({
  url: 'crm.finance.api.global_search',
  makeParams() {
    return { query: debouncedQuery.value, company: company.value, limit: 20 }
  },
})

const apiData = computed(
  () => searchResource.data || { records: [], navigate: [], reports: [], create: [] },
)

const navigateItems = computed(() =>
  (apiData.value.navigate || []).map((i) => ({
    name: 'nav-' + (i.section || i.label || i.key),
    title: i.label,
    description: i.subtitle || '',
    icon: LucideCompass,
    type: 'navigate',
    section: i.section || i.key,
  })),
)

const reportItems = computed(() => {
  if (!query.value || query.value.length < 2) return []
  const q = query.value.toLowerCase()
  return REPORTS.filter(
    (r) => r.roles.some((role) => props.userRoles.includes(role)) && r.label.toLowerCase().includes(q),
  )
    .slice(0, 5)
    .map((r) => ({
      name: 'report-' + r.report,
      title: r.label,
      description: r.group || '',
      icon: LucideBarChart2,
      type: 'report',
      url: buildReportUrl(r),
    }))
})

const recordItems = computed(() =>
  (apiData.value.records || []).map((i) => ({
    name: 'rec-' + i.doctype + '-' + i.name,
    title: i.label || i.name,
    description: i.doctype || '',
    icon: LucideFileText,
    type: 'record',
    url: i.url || '/app/' + slug(i.doctype) + '/' + encodeURIComponent(i.name),
  })),
)

const groups = computed(() => {
  const out = []
  if (navigateItems.value.length) out.push({ title: 'Navigate', items: navigateItems.value })
  if (reportItems.value.length) out.push({ title: 'Reports', items: reportItems.value })
  if (recordItems.value.length) out.push({ title: 'Records', items: recordItems.value })
  return out
})

const allItems = computed(() => groups.value.flatMap((g) => g.items))

function slug(dt) { return (dt || '').toLowerCase().replace(/\s+/g, '-') }

function buildReportUrl(r) {
  const base = '/app/query-report/' + encodeURIComponent(r.report)
  const params = {}
  for (const [k, v] of Object.entries(r.defaultFilters || {})) {
    params[k] = v === '__COMPANY__' ? company.value || '' : v
  }
  const qs = new URLSearchParams(params).toString()
  return qs ? base + '?' + qs : base
}

function onSelect(item) {
  if (!item) return
  if (item.type === 'navigate') emit('navigate', item.section)
  else if (item.url) window.open(item.url, '_blank')
  query.value = ''
  localShow.value = false
}
</script>
