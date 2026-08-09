<template>
  <div class="fc-finance-form pb-24">
    <!-- Page header -->
    <div class="mb-5">
      <p class="text-xs font-medium text-ink-gray-5">{{ name ? 'Editing' : 'New Document' }}</p>
      <h2 class="text-xl font-bold text-ink-gray-9 truncate">{{ name || 'New ' + doctype }}</h2>
    </div>

    <!-- Error banner -->
    <div
      v-if="crud.error.value || localError"
      class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
    >
      <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
      <span>{{ crud.error.value || localError }}</span>
    </div>

    <!-- Loading -->
    <div v-if="loadingDoc" class="space-y-4">
      <div v-for="n in 3" :key="n" class="h-40 bg-surface-gray-2 rounded-xl animate-pulse" />
    </div>

    <template v-else>
      <form class="space-y-5" @submit.prevent="onSave">
        <SectionCard
          v-for="sec in layout.sections"
          :key="sec.key"
          :title="sec.title"
          :icon="sec.icon"
          :tone="sectionTone(sec)"
          :hero="!!sec.hero"
          :collapsible="!!sec.collapsible"
          :collapsed="!!sec.collapsed"
          :badge="sectionBadge(sec)"
        >
          <!-- Fields section -->
          <div v-if="sec.kind === 'fields'" class="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
            <div
              v-for="f in sec.fields"
              :key="f.fieldname"
              :class="isProminent(f) ? 'md:col-span-2' : ''"
            >
              <FieldRenderer
                :field="f"
                :currency="doc.currency"
                :model-value="doc[f.fieldname]"
                :link-doctype="linkTargetFor(f)"
                @update:model-value="setField(f.fieldname, $event)"
              />
            </div>
          </div>

          <!-- Line items (hero) -->
          <LineItemsGrid
            v-else-if="sec.kind === 'lineItems'"
            :columns="sec.columns"
            :rows="doc[sec.tableField] || []"
            :currency="doc.currency"
            :qty-field="sec.qtyField"
            :rate-field="sec.rateField"
            :amount-field="sec.amountField"
            @update:rows="setField(sec.tableField, $event)"
          />

          <!-- Taxes -->
          <LineItemsGrid
            v-else-if="sec.kind === 'taxes'"
            :columns="sec.columns"
            :rows="doc[sec.tableField] || []"
            :currency="doc.currency"
            @update:rows="setField(sec.tableField, $event)"
          />

          <!-- Summary -->
          <SummaryBar
            v-else-if="sec.kind === 'summary'"
            :subtotal="subtotal"
            :tax="taxTotal"
            :grand-total="grandTotal"
            :currency="doc.currency"
            :notes="doc[layout.remarksField] || ''"
            :notes-label="layout.remarksLabel"
            :show-notes="!!layout.remarksField"
            @update:notes="setField(layout.remarksField, $event)"
          />
        </SectionCard>
      </form>
    </template>

    <!-- Sticky action bar -->
    <div
      v-if="!loadingDoc"
      class="fixed bottom-0 inset-x-0 z-30 bg-surface-white/95 backdrop-blur border-t border-outline-gray-2"
    >
      <div class="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between gap-3">
        <div class="hidden sm:flex items-center gap-2 text-sm text-ink-gray-5">
          <template v-if="layout.totals">
            <span>Grand Total</span>
            <span class="text-base font-bold text-ink-gray-9 tabular-nums">{{ fmt(grandTotal) }}</span>
          </template>
        </div>
        <div class="flex items-center gap-2 ml-auto">
          <Button variant="outline" theme="gray" label="Cancel" @click="$emit('close')" />
          <Button
            v-if="canSubmit"
            theme="green"
            variant="subtle"
            :loading="crud.loading.value"
            @click="onSubmit"
          >
            <template #prefix><FcIcon name="send" :size="15" /></template>
            Submit
          </Button>
          <Button variant="solid" theme="blue" :loading="crud.loading.value" @click="onSave">
            <template #prefix><FcIcon name="save" :size="15" /></template>
            Save
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Button, toast } from 'frappe-ui'
import FieldRenderer from './FieldRenderer.vue'
import LineItemsGrid from './LineItemsGrid.vue'
import SectionCard from './SectionCard.vue'
import SummaryBar from './SummaryBar.vue'
import FcIcon from './FcIcon.vue'
import { useCrud } from '../../composables/useCrud.js'
import { useCompanyContext } from '../../composables/useCompanyContext.js'
import { useCurrency } from '../../composables/useCurrency.js'
import { resolveLayout } from '../../constants/formLayouts.js'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, default: null },
  // Optional pre-filled document (e.g. an ERPNext mapped doc from a "Create From"
  // flow). When provided and there is no `name`, the form hydrates from the seed
  // instead of bare defaults, then saves through the normal insert path.
  seed: { type: Object, default: null },
})

const emit = defineEmits(['saved', 'close'])

const crud = useCrud(props.doctype)
const { company } = useCompanyContext()
const { formatCurrency } = useCurrency()

const layout = resolveLayout(props.doctype)
const loadingDoc = ref(true)
const localError = ref('')
const doc = reactive({})

// The first Link field in the first fields-section gets full-width prominence.
const prominentField = computed(() => {
  const first = layout.sections.find((s) => s.kind === 'fields')
  if (!first) return null
  const link = (first.fields || []).find((f) => f.type === 'link')
  return link?.fieldname || null
})
function isProminent(f) {
  return f.fieldname === prominentField.value
}

/* ---- Live totals ---- */
const totalsCfg = computed(() => layout.totals)
const subtotal = computed(() => {
  const cfg = totalsCfg.value
  if (!cfg) return 0
  const rows = doc[cfg.lineItemsField] || []
  return rows.reduce((s, r) => s + Number(r[cfg.qtyField] ?? 0) * Number(r[cfg.rateField] ?? 0), 0)
})
const taxTotal = computed(() => {
  const cfg = totalsCfg.value
  if (!cfg) return 0
  const rows = doc[cfg.taxRowsField] || []
  if (rows.length) {
    return rows.reduce((s, r) => s + Number(r[cfg.taxAmountField] ?? 0), 0)
  }
  return Number(doc[cfg.taxTotalField] ?? 0)
})
const grandTotal = computed(() => subtotal.value + taxTotal.value)

const canSubmit = computed(
  () => layout.isSubmittable && !!doc.name && Number(doc.docstatus || 0) === 0,
)

// Resolve the effective link target for a field. Dynamic Links (optionsField)
// take their target from a sibling field's current value; static links use
// their fixed `options`.
function linkTargetFor(f) {
  if (f.type !== 'link') return ''
  if (f.optionsField) return doc[f.optionsField] || ''
  return f.options || ''
}

function setField(fn, val) {
  const prev = doc[fn]
  doc[fn] = val
  // If this field is the target selector for a Dynamic Link (e.g. quotation_to
  // drives party_name), a changed value invalidates the dependent link's value
  // (a Customer name is not a valid Lead/Prospect). Clear the dependent field.
  if (val !== prev) {
    for (const f of layout.scalarFields) {
      if (f.optionsField === fn && doc[f.fieldname]) doc[f.fieldname] = null
    }
  }
}

function sectionBadge(sec) {
  if (sec.kind === 'lineItems' || sec.kind === 'taxes') {
    const n = (doc[sec.tableField] || []).length
    return n ? `${n}` : ''
  }
  return ''
}

// Colour-code section headers by role so a long form reads as distinct zones
// instead of a monotone stack. A layout may override with `sec.tone`.
// (No `info`/blue tone — this fork rebrands blue to red; neutral is the calm default.)
const SECTION_TONE = {
  lineItems: 'positive', // the value the doc is built from
  taxes: 'pending',      // adjustments / charges
  summary: 'positive',   // the resulting totals — a settled figure
  fields: 'neutral',     // header/meta fields
}
function sectionTone(sec) {
  if (sec.tone) return sec.tone
  return SECTION_TONE[sec.kind] || 'neutral'
}

/* ---- Load / seed ---- */
function seedDefaults() {
  const out = {}
  for (const f of layout.scalarFields) {
    if (f.default != null) out[f.fieldname] = f.default
    else out[f.fieldname] = f.type === 'check' ? 0 : null
  }
  for (const t of layout.childTables) out[t.tableField] = []
  if ('company' in out && !out.company && company.value) out.company = company.value
  return out
}

function hydrate(source) {
  for (const k of Object.keys(doc)) delete doc[k]
  Object.assign(doc, source)
}

// Strip Frappe meta flags + identity from a seed (e.g. an ERPNext mapped doc)
// so it always flows through the clean insert path. Extra business fields the
// layout doesn't render are preserved and ride along on save. Child-table rows
// are shallow-cleaned the same way (their name/docname must not survive insert).
function sanitizeSeed(source) {
  if (!source || typeof source !== 'object') return {}
  const clean = {}
  for (const [k, v] of Object.entries(source)) {
    if (k.startsWith('__')) continue // __islocal / __unsaved / __onload
    if (k === 'name' || k === 'amended_from') continue
    if (Array.isArray(v)) {
      clean[k] = v.map((row) =>
        row && typeof row === 'object' ? sanitizeSeed(row) : row,
      )
    } else {
      clean[k] = v
    }
  }
  return clean
}

onMounted(async () => {
  try {
    if (props.name) {
      const loaded = await crud.loadDoc(props.name)
      hydrate({ ...seedDefaults(), ...loaded })
    } else if (props.seed) {
      hydrate({ ...seedDefaults(), ...sanitizeSeed(props.seed) })
    } else {
      hydrate(seedDefaults())
    }
  } catch {
    localError.value = crud.error.value || 'Failed to load form.'
  } finally {
    loadingDoc.value = false
  }
})

async function persist() {
  const saved = await crud.saveDoc({ ...doc })
  hydrate({ ...doc, ...saved })
  return saved
}

async function onSave() {
  localError.value = ''
  try {
    const saved = await persist()
    toast.success('Saved ' + (saved.name || props.doctype))
    emit('saved', saved)
  } catch {
    toast.error(crud.error.value || 'Save failed')
  }
}

async function onSubmit() {
  localError.value = ''
  try {
    const saved = await persist()
    const submitted = await crud.submitDoc({ ...doc, name: saved.name })
    hydrate({ ...doc, ...submitted })
    toast.success('Submitted ' + saved.name)
    emit('saved', submitted)
  } catch {
    toast.error(crud.error.value || 'Submit failed')
  }
}

function fmt(v) {
  return formatCurrency(v ?? 0, doc.currency)
}
</script>
