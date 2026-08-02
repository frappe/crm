<template>
  <div v-if="hfrEnabled" class="hfr-panel flex flex-col gap-3">

    <!-- Search input -->
    <div class="relative flex items-center">
      <span class="absolute left-3 text-ink-gray-4 pointer-events-none">
        <svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="6.5" cy="6.5" r="4"/><path d="M10.5 10.5l3 3"/>
        </svg>
      </span>
      <input
        ref="inputRef"
        v-model="localQuery"
        type="text"
        class="w-full rounded-lg border border-outline-gray-2 bg-surface-white dark:bg-surface-gray-2
               pl-9 pr-9 py-2 text-p-sm text-ink-gray-8 placeholder:text-ink-gray-4
               focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
               transition-shadow"
        :placeholder="__('MFL code, FID, or registration number...')"
        autocomplete="off"
        @input="onInput"
        @keydown.enter.prevent="triggerSearch"
      />
      <span v-if="searching || fetchingDetail" class="absolute right-3 text-ink-gray-4 pointer-events-none">
        <svg class="size-4 animate-spin" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="8" cy="8" r="6" stroke-dasharray="25" stroke-dashoffset="10"/>
        </svg>
      </span>
      <button
        v-else-if="localQuery"
        class="absolute right-3 text-ink-gray-4 hover:text-ink-gray-7 transition-colors"
        @click="clearQuery"
      >
        <svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 4l8 8M12 4l-8 8"/>
        </svg>
      </button>
    </div>

    <!-- Results -->
    <div v-if="results.length" class="flex flex-col gap-1">
      <button
        v-for="r in results"
        :key="r.fid"
        class="group flex items-start gap-3 rounded-lg border border-outline-gray-2
               bg-surface-white dark:bg-surface-gray-2 px-3 py-2.5 text-left
               hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950
               transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        :disabled="fetchingDetail"
        @click="select(r)"
      >
        <span class="mt-0.5 shrink-0 size-8 rounded-md bg-surface-gray-2 dark:bg-surface-gray-3
                     flex items-center justify-center text-ink-gray-5
                     group-hover:bg-blue-100 dark:group-hover:bg-blue-900 transition-colors">
          <svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.25">
            <path d="M2 6.5V13h12V6.5M1 6h14M6 13V9h4v4"/><path d="M8 3l5 3H3l5-3z"/>
          </svg>
        </span>
        <div class="flex flex-col gap-0.5 min-w-0 flex-1">
          <span class="text-p-sm-medium text-ink-gray-8 truncate">{{ r.name }}</span>
          <div class="flex items-center gap-1.5 flex-wrap">
            <span v-if="r.mfl_code"
                  class="inline-flex items-center rounded px-1.5 py-0.5 text-p-xs
                         bg-surface-gray-2 dark:bg-surface-gray-3 text-ink-gray-6">
              MFL {{ r.mfl_code }}
            </span>
            <span v-if="r.level"
                  class="inline-flex items-center rounded px-1.5 py-0.5 text-p-xs
                         bg-surface-gray-2 dark:bg-surface-gray-3 text-ink-gray-6">
              {{ r.level }}
            </span>
            <span v-if="r.county" class="text-p-xs text-ink-gray-5">{{ r.county }}</span>
            <span v-if="r.owner_type" class="text-p-xs text-ink-gray-4">· {{ r.owner_type }}</span>
          </div>
        </div>
        <span class="shrink-0 mt-0.5 text-p-xs text-blue-500 opacity-0 group-hover:opacity-100
                     transition-opacity whitespace-nowrap">
          {{ __('Add →') }}
        </span>
      </button>
    </div>

    <!-- No results -->
    <div v-else-if="searched && !searching && localQuery.length >= 3"
         class="flex flex-col items-center gap-1 py-3 text-center">
      <svg class="size-7 text-ink-gray-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.25">
        <circle cx="10" cy="10" r="7"/><path d="M17 17l4 4"/><path d="M10 7v6M7 10h6"/>
      </svg>
      <p class="text-p-sm text-ink-gray-5">{{ __('No facility found') }}</p>
      <p class="text-p-xs text-ink-gray-4">{{ __('Check the code or fill manually') }}</p>
    </div>

    <!-- Pending rows (added but not yet saved) -->
    <div v-if="pendingRows.length" class="flex flex-col gap-1">
      <div class="text-p-xs-medium uppercase tracking-wider text-ink-gray-4">
        {{ __('Added ({0})', [pendingRows.length]) }}
      </div>
      <div
        v-for="row in pendingRows"
        :key="row.hfr_facility_id"
        class="flex items-center gap-2 rounded-lg border border-green-200 dark:border-green-800
               bg-green-50 dark:bg-green-950 px-3 py-2"
      >
        <div class="flex flex-col flex-1 min-w-0 gap-0.5">
          <span class="text-p-sm-medium text-ink-gray-8 truncate">{{ row.facility_name }}</span>
          <span class="text-p-xs text-ink-gray-5">
            <span v-if="row.mfl_code">MFL {{ row.mfl_code }} · </span>
            {{ row.hfr_county }}
            <span v-if="row.facility_owner_type"> · {{ row.facility_owner_type }}</span>
          </span>
        </div>
        <span class="shrink-0 text-p-xs bg-green-100 dark:bg-green-900
                     text-green-700 dark:text-green-300 rounded px-1.5 py-0.5">
          {{ __('Verified') }}
        </span>
        <button
          class="shrink-0 text-ink-gray-4 hover:text-red-500 transition-colors"
          :aria-label="__('Remove facility')"
          @click="removeRow(row.hfr_facility_id)"
        >
          <svg class="size-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4l8 8M12 4l-8 8"/>
          </svg>
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from 'vue'
import { createResource, toast } from 'frappe-ui'

const props = defineProps({
  doc: { type: Object, required: true },
  childDoctype: { type: String, required: true },
})

const emit = defineEmits(['row-added', 'row-removed'])

const hfrEnabled = inject('hfrEnabled', ref(false))

const localQuery = ref('')
const results = ref([])
const searching = ref(false)
const fetchingDetail = ref(false)
const searched = ref(false)
const inputRef = ref(null)
let debounceTimer = null

function detectSearchBy(val) {
  const v = (val || '').trim()
  if (/^FID-/i.test(v)) return 'facility_fid'
  if (/^[0-9]+$/.test(v)) return 'mfl_code'
  return 'registration_number'
}

const searchResource = createResource({
  url: 'crm.api.hfr.search_facility',
  onSuccess(data) {
    results.value = data || []
    searching.value = false
    searched.value = true
  },
  onError() {
    results.value = []
    searching.value = false
    searched.value = true
  },
})

const detailResource = createResource({
  url: 'crm.api.hfr.get_facility_detail',
  onSuccess(data) {
    if (!data) { fetchingDetail.value = false; return }
    const fid = data.hfr_facility_id
    const existing = (props.doc.facilities || []).find(r => r.hfr_facility_id === fid)
    if (existing) {
      toast.warning(__('This facility is already in the list.'))
      fetchingDetail.value = false
      return
    }
    if (!props.doc.facilities) props.doc.facilities = []
    props.doc.facilities.push({
      doctype: props.childDoctype,
      hfr_facility_id: fid,
      facility_name: data.organization_name,
      mfl_code: data.mfl_code,
      facility_type: data.facility_type,
      facility_category: data.facility_category,
      facility_level: data.facility_level,
      facility_owner: data.facility_owner,
      facility_owner_type: data.facility_owner_type,
      regulatory_body: data.regulatory_body,
      registration_number: data.registration_number,
      operational_status: data.operational_status,
      hfr_county: data.hfr_county,
      hfr_sub_county: data.hfr_sub_county,
      hfr_ward: data.hfr_ward,
      latitude: data.latitude,
      longitude: data.longitude,
      license_number: data.license_number,
      license_expiry: data.license_expiry,
      facility_standing: data.facility_standing,
      number_of_beds: data.number_of_beds,
      hfr_sync_status: 'HFR Verified',
    })
    results.value = []
    localQuery.value = ''
    searched.value = false
    fetchingDetail.value = false
    emit('row-added', data)
  },
  onError() { fetchingDetail.value = false },
})

// Rows appended in this session (no `name` yet — unsaved)
const pendingRows = computed(() =>
  (props.doc.facilities || []).filter(r => !r.name)
)

function onInput() {
  searched.value = false
  results.value = []
  clearTimeout(debounceTimer)
  if (localQuery.value.length < 3) return
  debounceTimer = setTimeout(() => triggerSearch(), 600)
}

function triggerSearch() {
  if ((localQuery.value || '').length < 3) return
  clearTimeout(debounceTimer)
  searching.value = true
  results.value = []
  searchResource.submit({
    query: localQuery.value.trim(),
    search_by: detectSearchBy(localQuery.value),
  })
}

function select(r) {
  const already = (props.doc.facilities || []).find(row => row.hfr_facility_id === r.fid)
  if (already) {
    toast.warning(__('This facility is already in the list.'))
    return
  }
  fetchingDetail.value = true
  detailResource.submit({ fid: r.fid })
}

function removeRow(fid) {
  props.doc.facilities = (props.doc.facilities || []).filter(
    r => r.hfr_facility_id !== fid
  )
  emit('row-removed', fid)
}

function clearQuery() {
  localQuery.value = ''
  results.value = []
  searched.value = false
  inputRef.value?.focus()
}

watch(hfrEnabled, (v) => {
  if (v) setTimeout(() => inputRef.value?.focus(), 50)
}, { immediate: true })
</script>
