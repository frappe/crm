<template>
  <div class="fc-summary grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- Notes (left) -->
    <div class="lg:col-span-2">
      <label v-if="showNotes" class="block text-xs font-medium text-ink-gray-5 mb-1.5">
        {{ notesLabel }}
      </label>
      <textarea
        v-if="showNotes && !readOnly"
        :value="notes ?? ''"
        rows="4"
        :placeholder="'Add ' + notesLabel.toLowerCase() + '...'"
        class="w-full text-sm border border-outline-gray-2 rounded-lg px-3 py-2 bg-surface-white text-ink-gray-8 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none dark:bg-surface-gray-2 dark:text-ink-gray-7 dark:border-outline-gray-3"
        @input="$emit('update:notes', $event.target.value)"
      />
      <p
        v-else-if="showNotes"
        class="text-sm text-ink-gray-7 whitespace-pre-line min-h-[40px]"
      >{{ notes || '—' }}</p>
    </div>

    <!-- Totals (right) -->
    <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-4 space-y-2.5">
      <div class="flex items-center justify-between text-sm">
        <span class="text-ink-gray-5">Subtotal</span>
        <span class="font-medium text-ink-gray-7 tabular-nums">{{ fmt(subtotal) }}</span>
      </div>

      <!-- Single tax row (collapsed) or per-row breakdown -->
      <template v-if="taxRows && taxRows.length > 1">
        <div
          v-for="(row, i) in visibleTaxRows"
          :key="i"
          class="flex items-center justify-between text-sm"
        >
          <span class="text-ink-gray-5 truncate mr-2">{{ row.label }}</span>
          <span class="font-medium text-ink-gray-7 tabular-nums">{{ fmt(row.amount) }}</span>
        </div>
      </template>
      <div v-else class="flex items-center justify-between text-sm">
        <span class="text-ink-gray-5">Tax</span>
        <span class="font-medium text-ink-gray-7 tabular-nums">{{ fmt(tax) }}</span>
      </div>

      <div class="pt-2.5 border-t border-outline-gray-2 flex items-center justify-between bg-surface-blue-6 -mx-4 -mb-4 px-4 pb-4 rounded-b-xl">
        <span class="text-sm font-semibold text-ink-gray-7">Grand Total</span>
        <span class="text-xl font-bold text-ink-gray-9 tabular-nums">{{ fmt(grandTotal) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useCurrency } from '../../composables/useCurrency.js'

const props = defineProps({
  subtotal: { type: Number, default: 0 },
  tax: { type: Number, default: 0 },
  grandTotal: { type: Number, default: 0 },
  currency: { type: String, default: '' },
  notes: { type: String, default: '' },
  notesLabel: { type: String, default: 'Notes' },
  showNotes: { type: Boolean, default: true },
  readOnly: { type: Boolean, default: false },
  // Optional: pass full tax rows for per-line breakdown (FC-16).
  // Each item: { description, account_head, tax_amount, rate }
  taxRows: { type: Array, default: null },
})

defineEmits(['update:notes'])

const { formatCurrency } = useCurrency()
function fmt(v) {
  return formatCurrency(v ?? 0, props.currency)
}

// Build display rows: skip zero-amount rows, label from description or account_head.
const visibleTaxRows = computed(() => {
  if (!props.taxRows || props.taxRows.length <= 1) return []
  return props.taxRows
    .filter((r) => Number(r.tax_amount ?? 0) !== 0)
    .map((r) => ({
      label: r.description || r.account_head || 'Tax',
      amount: Number(r.tax_amount ?? 0),
    }))
})
</script>
