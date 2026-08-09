<template>
  <div class="fc-line-items">
    <!-- Desktop grid -->
    <div v-if="!isMobile" class="rounded-lg border border-outline-gray-1 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-gray-2 border-b border-outline-gray-1">
            <th class="px-3 py-2.5 text-left text-[11px] font-semibold text-ink-gray-5 uppercase tracking-wider w-8">#</th>
            <th
              v-for="col in columns"
              :key="col.fieldname"
              class="px-3 py-2.5 text-[11px] font-semibold text-ink-gray-5 uppercase tracking-wider whitespace-nowrap"
              :class="isNumericCol(col) ? 'text-right' : 'text-left'"
            >
              {{ col.label }}<span v-if="col.required" class="text-red-500 ml-0.5">*</span>
            </th>
            <th v-if="showAmount" class="px-3 py-2.5 text-right text-[11px] font-semibold text-ink-gray-5 uppercase tracking-wider">Amount</th>
            <th v-if="!readOnly" class="px-2 py-2.5 w-10" />
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr v-if="!rows.length">
            <td :colspan="totalCols" class="px-3 py-8 text-center">
              <div class="flex flex-col items-center gap-1.5 text-ink-gray-4">
                <FcIcon name="list" :size="22" />
                <span class="text-sm">No line items yet.</span>
                <button
                  v-if="!readOnly"
                  type="button"
                  class="mt-1 text-xs font-medium text-blue-600 hover:underline"
                  @click="addRow"
                >+ Add your first line</button>
              </div>
            </td>
          </tr>
          <tr
            v-for="(row, idx) in rows"
            :key="idx"
            class="group align-top hover:bg-surface-gray-1 transition-colors"
          >
            <td class="px-3 py-2 text-xs text-ink-gray-4 tabular-nums">{{ idx + 1 }}</td>
            <td
              v-for="col in columns"
              :key="col.fieldname"
              class="px-3 py-2"
              :class="isNumericCol(col) ? 'text-right' : ''"
            >
              <FieldRenderer
                :field="col"
                :show-label="false"
                :force-read-only="readOnly"
                :currency="currency"
                :model-value="row[col.fieldname]"
                @update:model-value="updateCell(idx, col.fieldname, $event)"
              />
            </td>
            <td v-if="showAmount" class="px-3 py-2 text-right">
              <span class="text-sm font-semibold text-ink-gray-8 tabular-nums">{{ formatCurrency(rowAmount(row), currency) }}</span>
            </td>
            <td v-if="!readOnly" class="px-2 py-2 text-right">
              <button
                type="button"
                class="opacity-0 group-hover:opacity-100 focus:opacity-100 text-ink-gray-4 hover:text-red-600 transition-opacity p-1 rounded"
                title="Remove line"
                @click="removeRow(idx)"
              >
                <FcIcon name="trash" :size="15" />
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="rows.length && showAmount">
          <tr class="border-t border-outline-gray-1 bg-surface-gray-2">
            <td :colspan="columns.length + 1" class="px-3 py-2.5 text-right text-xs font-medium text-ink-gray-5">
              {{ rows.length }} {{ rows.length === 1 ? 'line' : 'lines' }} · Total
            </td>
            <td class="px-3 py-2.5 text-right text-sm font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(runningTotal, currency) }}</td>
            <td v-if="!readOnly" />
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Mobile stacked cards -->
    <div v-else class="space-y-3">
      <div v-if="!rows.length" class="rounded-lg border border-dashed border-outline-gray-2 py-8 text-center text-sm text-ink-gray-4">
        No line items yet.
      </div>
      <div
        v-for="(row, idx) in rows"
        :key="idx"
        class="rounded-lg border border-outline-gray-1 bg-surface-white p-3"
      >
        <div class="flex items-center justify-between mb-2.5">
          <span class="text-xs font-semibold text-ink-gray-5">Line {{ idx + 1 }}</span>
          <div class="flex items-center gap-3">
            <span v-if="showAmount" class="text-sm font-bold text-ink-gray-8 tabular-nums">{{ formatCurrency(rowAmount(row), currency) }}</span>
            <button
              v-if="!readOnly"
              type="button"
              class="text-ink-gray-4 hover:text-red-600"
              @click="removeRow(idx)"
            >
              <FcIcon name="trash" :size="15" />
            </button>
          </div>
        </div>
        <div class="space-y-2.5">
          <FieldRenderer
            v-for="col in columns"
            :key="col.fieldname"
            :field="col"
            :show-label="true"
            :force-read-only="readOnly"
            :currency="currency"
            :model-value="row[col.fieldname]"
            @update:model-value="updateCell(idx, col.fieldname, $event)"
          />
        </div>
      </div>
      <div v-if="rows.length && showAmount" class="flex items-center justify-between px-1 pt-1">
        <span class="text-xs font-medium text-ink-gray-5">Total</span>
        <span class="text-base font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(runningTotal, currency) }}</span>
      </div>
    </div>

    <!-- Add line -->
    <button
      v-if="!readOnly && rows.length"
      type="button"
      class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
      @click="addRow"
    >
      <FcIcon name="plus" :size="16" /> Add line
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import FieldRenderer from './FieldRenderer.vue'
import FcIcon from './FcIcon.vue'
import { useBreakpoint } from '../../composables/useBreakpoint.js'
import { useCurrency } from '../../composables/useCurrency.js'

const props = defineProps({
  // Normalized column field objects from formLayouts.js.
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  readOnly: { type: Boolean, default: false },
  currency: { type: String, default: '' },
  // Live-calc field mapping (from layout config).
  qtyField: { type: String, default: '' },
  rateField: { type: String, default: '' },
  amountField: { type: String, default: '' },
})

const emit = defineEmits(['update:rows'])

const { isMobile } = useBreakpoint()
const { formatCurrency } = useCurrency()

const showAmount = computed(() => !!(props.qtyField && props.rateField))

// Curated columns from layout config; exclude the computed amount field (it is
// rendered as its own running-total column) to avoid duplication.
const columns = computed(() =>
  (props.columns || []).filter((f) => f.fieldname !== props.amountField),
)

const totalCols = computed(
  () => columns.value.length + 1 + (showAmount.value ? 1 : 0) + (props.readOnly ? 0 : 1),
)

function isNumericCol(col) {
  return ['int', 'float', 'currency'].includes(col.type)
}

function rowAmount(row) {
  if (!showAmount.value) return 0
  const qty = Number(row[props.qtyField] ?? 0)
  const rate = Number(row[props.rateField] ?? 0)
  return qty * rate
}

const runningTotal = computed(() => props.rows.reduce((sum, r) => sum + rowAmount(r), 0))

function seedRow() {
  const row = {}
  for (const f of props.columns || []) row[f.fieldname] = f.type === 'check' ? 0 : null
  if (props.amountField) row[props.amountField] = 0
  return row
}

function addRow() {
  emit('update:rows', [...props.rows, seedRow()])
}

function removeRow(idx) {
  const next = props.rows.slice()
  next.splice(idx, 1)
  emit('update:rows', next)
}

function updateCell(idx, fieldname, value) {
  const next = props.rows.slice()
  const updated = { ...next[idx], [fieldname]: value }
  // Keep the stored amount in sync so the saved doc carries a value pre-server-recompute.
  if (props.amountField && (fieldname === props.qtyField || fieldname === props.rateField)) {
    const qty = Number(fieldname === props.qtyField ? value : updated[props.qtyField] ?? 0)
    const rate = Number(fieldname === props.rateField ? value : updated[props.rateField] ?? 0)
    updated[props.amountField] = qty * rate
  }
  next[idx] = updated
  emit('update:rows', next)
}

defineExpose({ runningTotal })
</script>
