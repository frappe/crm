<template>
  <Section title="Products">
    <template #actions>
      <span class="text-sm text-ink-gray-5">
        Net Total: <strong class="text-ink-gray-9">{{ formatCurrency(doc.net_total) }}</strong>
      </span>
    </template>

    <div v-if="!doc.products?.length" class="py-8 text-center text-sm text-ink-gray-5">
      No products added
    </div>

    <table v-else class="w-full text-sm">
      <thead class="border-b border-outline-gray-2">
        <tr>
          <th class="pb-2 text-left font-medium text-ink-gray-7">Product</th>
          <th class="pb-2 text-left font-medium text-ink-gray-7">Remark</th>
          <th class="pb-2 text-right font-medium text-ink-gray-7">Qty</th>
          <th class="pb-2 text-right font-medium text-ink-gray-7">Price</th>
          <th class="pb-2 text-right font-medium text-ink-gray-7">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in doc.products" :key="p.name" class="border-b border-outline-gray-1">
          <td class="py-3 text-ink-gray-9">{{ p.product }}</td>
          <td class="py-3 text-ink-gray-7">{{ p.remark || '-' }}</td>
          <td class="py-3 text-right text-ink-gray-7">{{ p.qty }}</td>
          <td class="py-3 text-right text-ink-gray-7">{{ formatCurrency(p.price) }}</td>
          <td class="py-3 text-right font-medium text-ink-gray-9">{{ formatCurrency(p.amount) }}</td>
        </tr>
      </tbody>
      <tfoot class="border-t-2 border-outline-gray-3">
        <tr>
          <td colspan="4" class="pt-3 text-right font-semibold text-ink-gray-9">Total</td>
          <td class="pt-3 text-right font-bold text-ink-gray-9">{{ formatCurrency(doc.net_total) }}</td>
        </tr>
      </tfoot>
    </table>
  </Section>
</template>

<script setup>
import { computed } from 'vue'
import Section from './shared/Section.vue'

const props = defineProps(['quotation'])
const doc = computed(() => props.quotation.doc)

function formatCurrency(amount) {
  if (!amount) return '-'
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(amount)
}
</script>