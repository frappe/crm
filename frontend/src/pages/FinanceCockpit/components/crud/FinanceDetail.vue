<template>
  <div class="fc-finance-detail pb-6">
    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div class="h-24 bg-surface-gray-2 rounded-xl animate-pulse" />
      <div class="h-64 bg-surface-gray-2 rounded-xl animate-pulse" />
    </div>

    <template v-else-if="doc">
      <!-- Error banner -->
      <div
        v-if="crud.error.value"
        class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
      >
        <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
        <span>{{ crud.error.value }}</span>
      </div>

      <!-- Document header -->
      <div class="rounded-xl border border-outline-gray-1 bg-surface-white shadow-sm overflow-hidden">
        <div class="p-5 sm:p-6 flex flex-col lg:flex-row lg:items-center gap-5">
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <span class="flex items-center justify-center w-11 h-11 rounded-xl bg-surface-gray-3 text-ink-gray-7 flex-shrink-0">
              <FcIcon name="receipt" :size="22" />
            </span>
            <div class="min-w-0">
              <div class="flex items-center gap-2.5 flex-wrap">
                <h2 class="text-xl font-bold text-ink-gray-9 truncate">{{ name }}</h2>
                <StatusBadge v-if="statusValue" :status="statusValue" />
              </div>
              <p v-if="subtitle" class="text-sm text-ink-gray-5 mt-0.5 truncate">{{ subtitle }}</p>
            </div>
          </div>

          <!-- Key amount -->
          <div v-if="keyAmount !== null" class="lg:text-right">
            <p class="text-xs font-medium text-ink-gray-5">{{ keyAmountLabel }}</p>
            <p class="text-2xl font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(keyAmount, doc.currency) }}</p>
          </div>

          <!-- Actions (RBAC-gated, visible-but-disabled) -->
          <div class="flex items-center gap-2 flex-wrap">
            <Button
              variant="outline"
              theme="gray"
              :disabled="!canWrite || isCancelled"
              :title="!canWrite ? 'No permission to edit' : ''"
              @click="canWrite && !isCancelled && $emit('edit')"
            >
              <template #prefix><FcIcon name="edit" :size="14" /></template>
              Edit
            </Button>
            <Button
              v-if="isSubmittable && docstatus === 0"
              theme="green"
              variant="subtle"
              :loading="busy"
              :disabled="!canSubmit"
              :title="!canSubmit ? 'No permission to submit' : ''"
              @click="onSubmit"
            >
              <template #prefix><FcIcon name="send" :size="14" /></template>
              Submit
            </Button>
            <Button
              v-if="isSubmittable && docstatus === 1"
              theme="gray"
              variant="outline"
              :loading="busy"
              :disabled="!canCancel"
              :title="!canCancel ? 'No permission to cancel' : ''"
              @click="onCancel"
            >
              <template #prefix><FcIcon name="x" :size="14" /></template>
              Cancel
            </Button>
            <Button
              theme="red"
              variant="subtle"
              :loading="busy"
              :disabled="!canDelete"
              :title="!canDelete ? 'No permission to delete' : ''"
              @click="onDelete"
            >
              <template #prefix><FcIcon name="trash" :size="14" /></template>
              Delete
            </Button>
          </div>
        </div>

        <!-- Summary strip: key facts -->
        <div class="border-t border-outline-gray-1 bg-surface-gray-1 px-5 sm:px-6 py-3 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <div v-for="fact in summaryFacts" :key="fact.fieldname" class="min-w-0">
            <dt class="text-[11px] font-medium text-ink-gray-5 uppercase tracking-wide">{{ fact.label }}</dt>
            <dd class="text-sm font-medium text-ink-gray-8 mt-0.5 truncate" :class="fact.numeric ? 'tabular-nums' : ''">{{ fact.display }}</dd>
          </div>
        </div>
      </div>

      <!-- Detail sections -->
      <div class="mt-5 space-y-5">
        <template v-for="sec in layout.sections" :key="sec.key">
          <!-- Line items / taxes -->
          <SectionCard
            v-if="sec.kind === 'lineItems' || sec.kind === 'taxes'"
            :title="sec.title"
            :icon="sec.icon"
            :tone="sec.kind === 'lineItems' ? 'positive' : 'pending'"
            :badge="(doc[sec.tableField] || []).length || ''"
          >
            <LineItemsGrid
              :columns="sec.columns"
              :rows="doc[sec.tableField] || []"
              :currency="doc.currency"
              :read-only="true"
              :qty-field="sec.kind === 'lineItems' ? sec.qtyField : ''"
              :rate-field="sec.kind === 'lineItems' ? sec.rateField : ''"
              :amount-field="sec.kind === 'lineItems' ? sec.amountField : ''"
            />
          </SectionCard>

          <!-- Summary -->
          <SectionCard v-else-if="sec.kind === 'summary'" :title="sec.title" :icon="sec.icon" tone="positive">
            <SummaryBar
              :subtotal="subtotal"
              :tax="taxTotal"
              :grand-total="grandTotal"
              :currency="doc.currency"
              :notes="doc[layout.remarksField] || ''"
              :notes-label="layout.remarksLabel"
              :show-notes="!!layout.remarksField"
              :read-only="true"
            />
          </SectionCard>
        </template>

        <!-- Configured scalar details -->
        <SectionCard v-if="detailFields.length" title="Details" icon="file-text" tone="neutral">
          <dl class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4">
            <div v-for="f in detailFields" :key="f.fieldname" class="flex flex-col min-w-0">
              <dt class="text-xs font-medium text-ink-gray-5">{{ f.label }}</dt>
              <dd class="text-sm text-ink-gray-8 mt-0.5 truncate" :class="isNum(f) ? 'tabular-nums' : ''">
                <template v-if="f.type === 'check'">{{ doc[f.fieldname] ? 'Yes' : 'No' }}</template>
                <template v-else-if="f.type === 'currency'">{{ formatCurrency(doc[f.fieldname], doc.currency) }}</template>
                <template v-else>{{ displayVal(doc[f.fieldname]) }}</template>
              </dd>
            </div>
          </dl>
        </SectionCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Button, toast, dialog } from 'frappe-ui'
import StatusBadge from './StatusBadge.vue'
import SectionCard from './SectionCard.vue'
import SummaryBar from './SummaryBar.vue'
import LineItemsGrid from './LineItemsGrid.vue'
import FcIcon from './FcIcon.vue'
import { useCrud } from '../../composables/useCrud.js'
import { useCurrency } from '../../composables/useCurrency.js'
import { useBoot } from '../../composables/useBoot.js'
import { resolveLayout, isNumericType } from '../../constants/formLayouts.js'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
})

const emit = defineEmits(['edit', 'deleted', 'close'])

const crud = useCrud(props.doctype)
const { formatCurrency } = useCurrency()
const { getRoles, isAdministrator } = useBoot()

const layout = resolveLayout(props.doctype)
const doc = ref(null)
const loading = ref(true)
const busy = ref(false)

/* ---- Header facets ---- */
const statusValue = computed(() => doc.value?.[layout.statusField] || '')
const isSubmittable = computed(() => layout.isSubmittable)
const docstatus = computed(() => Number(doc.value?.docstatus || 0))
const isCancelled = computed(() => docstatus.value === 2)

const subtitle = computed(() => {
  const d = doc.value
  if (!d) return ''
  return d.customer || d.supplier || d.party || d.title || ''
})

const totalsCfg = computed(() => layout.totals)
const keyAmountLabel = computed(() => (isSubmittable.value ? 'Grand Total' : 'Amount'))
const keyAmount = computed(() => {
  const d = doc.value
  if (!d) return null
  if (d.grand_total != null) return d.grand_total
  if (d.outstanding_amount != null) return d.outstanding_amount
  if (d.total != null) return d.total
  return null
})

const subtotal = computed(() => {
  const cfg = totalsCfg.value
  const d = doc.value
  if (!cfg || !d) return 0
  if (d[cfg.subtotalField] != null) return Number(d[cfg.subtotalField])
  const rows = d[cfg.lineItemsField] || []
  return rows.reduce((s, r) => s + Number(r[cfg.qtyField] ?? 0) * Number(r[cfg.rateField] ?? 0), 0)
})
const taxTotal = computed(() => {
  const cfg = totalsCfg.value
  const d = doc.value
  if (!cfg || !d) return 0
  if (d[cfg.taxTotalField] != null) return Number(d[cfg.taxTotalField])
  const rows = d[cfg.taxRowsField] || []
  return rows.reduce((s, r) => s + Number(r[cfg.taxAmountField] ?? 0), 0)
})
const grandTotal = computed(() => {
  const cfg = totalsCfg.value
  const d = doc.value
  if (cfg && d && d[cfg.grandTotalField] != null) return Number(d[cfg.grandTotalField])
  return subtotal.value + taxTotal.value
})

/* ---- Summary strip: prominent scalar facts from configured fields sections ---- */
const summaryFacts = computed(() => {
  if (!doc.value) return []
  const fields = []
  for (const sec of layout.sections) {
    if (sec.kind === 'fields') fields.push(...(sec.fields || []))
  }
  return fields
    .filter((f) => f.type !== 'check' && f.type !== 'textarea')
    .slice(0, 5)
    .map((f) => ({
      fieldname: f.fieldname,
      label: f.label,
      numeric: isNum(f),
      display:
        f.type === 'currency'
          ? formatCurrency(doc.value[f.fieldname], doc.value.currency)
          : displayVal(doc.value[f.fieldname]),
    }))
})

// Configured scalar fields not already shown in the summary strip.
const detailFields = computed(() => {
  if (!doc.value) return []
  const shown = new Set(summaryFacts.value.map((f) => f.fieldname))
  if (layout.remarksField) shown.add(layout.remarksField)
  const seen = new Set()
  const out = []
  for (const sec of layout.sections) {
    if (sec.kind !== 'fields') continue
    for (const f of sec.fields || []) {
      if (shown.has(f.fieldname) || seen.has(f.fieldname)) continue
      seen.add(f.fieldname)
      const v = doc.value[f.fieldname]
      if (v === null || v === undefined || v === '') continue
      out.push(f)
    }
  }
  return out
})

function isNum(f) {
  return isNumericType(f.type)
}
function displayVal(v) {
  return v === null || v === undefined || v === '' ? '—' : v
}

/* ---- RBAC ---- */
const roles = computed(() => getRoles())
const isElevated = computed(
  () =>
    isAdministrator() ||
    roles.value.includes('System Manager') ||
    roles.value.includes('Finance Manager') ||
    roles.value.includes('Accounts Manager'),
)
const canWrite = computed(() => isElevated.value || roles.value.includes('Accounts User'))
const canSubmit = computed(() => isElevated.value)
const canCancel = computed(() => isElevated.value)
const canDelete = computed(() => isElevated.value)

/* ---- Data ---- */
async function load() {
  loading.value = true
  try {
    doc.value = await crud.loadDoc(props.name)
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function onSubmit() {
  busy.value = true
  try {
    await crud.submitDoc({ ...doc.value })
    toast.success('Submitted ' + props.name)
    await load()
  } catch {
    toast.error(crud.error.value || 'Submit failed')
  } finally {
    busy.value = false
  }
}

async function onCancel() {
  busy.value = true
  try {
    await crud.cancelDoc(props.name)
    toast.success('Cancelled ' + props.name)
    await load()
  } catch {
    toast.error(crud.error.value || 'Cancel failed')
  } finally {
    busy.value = false
  }
}

function onDelete() {
  dialog.danger({
    title: 'Delete ' + props.name + '?',
    message: 'This action cannot be undone.',
    onConfirm: async () => {
      busy.value = true
      try {
        await crud.deleteDoc(props.name)
        toast.success('Deleted ' + props.name)
        emit('deleted', props.name)
      } catch {
        toast.error(crud.error.value || 'Delete failed')
      } finally {
        busy.value = false
      }
    },
  })
}
</script>
