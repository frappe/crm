<template>
  <div class="fc-create-from pb-24">
    <!-- Header -->
    <div class="mb-5">
      <p class="text-xs font-medium text-ink-gray-5">New Document</p>
      <h2 class="text-xl font-bold text-ink-gray-9">{{ flow.label }}</h2>
      <p class="text-sm text-ink-gray-5 mt-0.5">
        Pick a submitted {{ flow.sourceLabel }} to pre-fill a new {{ targetLabel }}. You can
        review and edit every field before saving.
      </p>
    </div>

    <!-- Error banner (mapper throws land here — e.g. expired-quote guard) -->
    <div
      v-if="errorMsg"
      class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
    >
      <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
      <span>{{ errorMsg }}</span>
    </div>

    <SectionCard :title="'Source ' + flow.sourceLabel" icon="file-text" hero>
      <div class="max-w-xl">
        <label class="block text-xs font-medium text-ink-gray-6 mb-1">
          {{ flow.sourceLabel }}<span class="text-red-500 ml-0.5">*</span>
        </label>
        <Combobox
          :model-value="source"
          :options="sourceOptions"
          :loading="listRes.loading"
          :placeholder="'Search ' + flow.sourceLabel + '...'"
          @update:model-value="onSelect"
          @update:query="onQuery"
        />
        <p class="text-xs text-ink-gray-4 mt-2">
          Only submitted {{ flow.sourceLabel }} records for the current company are listed.
        </p>

        <!-- Mapping in progress -->
        <div v-if="mapping" class="flex items-center gap-2 text-sm text-ink-gray-5 mt-4">
          <span class="w-4 h-4 border-2 border-outline-gray-4 border-t-transparent rounded-full animate-spin" />
          Preparing {{ targetLabel }} from {{ source }}…
        </div>
      </div>
    </SectionCard>

    <!-- Sticky action bar (Cancel only — advancing happens on select) -->
    <div class="fixed bottom-0 inset-x-0 z-30 bg-surface-white/95 backdrop-blur border-t border-outline-gray-2">
      <div class="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-end gap-2">
        <Button variant="outline" theme="gray" label="Cancel" @click="$emit('close')" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Button, Combobox, createResource, debounce } from 'frappe-ui'
import SectionCard from './SectionCard.vue'
import FcIcon from './FcIcon.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'
import { useMappedDoc } from '../../composables/useMappedDoc.js'

const props = defineProps({
  // Flow config: { key, label, sourceDoctype, sourceLabel, subtitleField, mapMethod, targetDoctype }
  flow: { type: Object, required: true },
})

const emit = defineEmits(['mapped', 'close'])

const { company } = useCompanyContext()
const { mapDoc } = useMappedDoc()

const source = ref(null)
const mapping = ref(false)
const errorMsg = ref('')

const targetLabel = computed(() => props.flow.targetDoctype)

/* ---- Source search (submitted-only, company-scoped, native get_list) ---- */
const sourceResults = ref([])
const listRes = createResource({ url: 'frappe.client.get_list' })

const sourceOptions = computed(() => {
  const opts = sourceResults.value.slice()
  if (source.value && !opts.some((o) => o.value === source.value)) {
    opts.unshift({ label: source.value, value: source.value })
  }
  return opts
})

// Monotonic request id so a slow reply for a stale query can't clobber the list.
let req = 0

async function runQuery(query) {
  const my = ++req
  // If the flow supplies explicit sourceFilters, use them directly (no company/docstatus
  // defaults). Otherwise fall back to the standard company + docstatus=1 filters —
  // but skip the company filter if the company context hasn't resolved yet.
  let filters
  if (props.flow.sourceFilters) {
    filters = props.flow.sourceFilters
  } else {
    if (!company.value) {
      sourceResults.value = []
      return
    }
    filters = [
      ['company', '=', company.value],
      ['docstatus', '=', 1],
    ]
  }

  const subtitle = props.flow.subtitleField
  const fields = ['name']
  if (subtitle) fields.push(subtitle)
  // Search across the document id AND the human-facing party field so typing a
  // customer/party name matches (ids like SAL-QTN-2026-00004 rarely get typed).
  const params = {
    doctype: props.flow.sourceDoctype,
    filters: JSON.stringify(filters),
    fields: JSON.stringify(fields),
    limit_page_length: 20,
    order_by: 'modified desc',
  }
  if (query) {
    const orFilters = [['name', 'like', `%${query}%`]]
    if (subtitle) orFilters.push([subtitle, 'like', `%${query}%`])
    params.or_filters = JSON.stringify(orFilters)
  }
  try {
    const rows = await listRes.submit(params)
    if (my !== req) return
    sourceResults.value = (rows || []).map((r) => ({
      label: subtitle && r[subtitle] ? `${r.name} · ${r[subtitle]}` : r.name,
      value: r.name,
    }))
  } catch {
    if (my === req) sourceResults.value = []
  }
}

const onQuery = debounce(runQuery, 250)

async function onSelect(val) {
  source.value = val
  if (!val) return
  errorMsg.value = ''
  mapping.value = true
  try {
    const doc = await mapDoc(props.flow.mapMethod, val)
    emit('mapped', doc)
  } catch (err) {
    // readableError already normalized inside useMappedDoc; surface the message.
    errorMsg.value =
      (err && (Array.isArray(err.messages) ? err.messages.join('\n') : err.message)) ||
      `Could not prepare a ${targetLabel.value} from ${val}.`
    source.value = null
  } finally {
    mapping.value = false
  }
}

// Prefetch an initial page immediately (no debounce for the first paint), and
// re-run once the company context resolves so the picker is never stuck empty.
runQuery('')
watch(company, () => runQuery(''))
</script>
