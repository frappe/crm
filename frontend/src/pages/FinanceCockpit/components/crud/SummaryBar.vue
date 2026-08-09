<template>
  <div class="fc-summary grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- Notes (left) -->
    <div class="lg:col-span-2">
      <label v-if="showNotes" class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">
        {{ notesLabel }}
      </label>
      <textarea
        v-if="showNotes && !readOnly"
        :value="notes ?? ''"
        rows="4"
        :placeholder="'Add ' + notesLabel.toLowerCase() + '...'"
        class="w-full text-sm border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
        @input="$emit('update:notes', $event.target.value)"
      />
      <p
        v-else-if="showNotes"
        class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line min-h-[40px]"
      >{{ notes || '—' }}</p>
    </div>

    <!-- Totals (right) -->
    <div class="rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 p-4 space-y-2.5">
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-500 dark:text-gray-400">Subtotal</span>
        <span class="font-medium text-gray-800 dark:text-gray-200 tabular-nums">{{ fmt(subtotal) }}</span>
      </div>
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-500 dark:text-gray-400">Tax</span>
        <span class="font-medium text-gray-800 dark:text-gray-200 tabular-nums">{{ fmt(tax) }}</span>
      </div>
      <div class="pt-2.5 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">Grand Total</span>
        <span class="text-xl font-bold text-gray-900 dark:text-gray-50 tabular-nums">{{ fmt(grandTotal) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
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
})

defineEmits(['update:notes'])

const { formatCurrency } = useCurrency()
function fmt(v) {
  return formatCurrency(v ?? 0, props.currency)
}
</script>
