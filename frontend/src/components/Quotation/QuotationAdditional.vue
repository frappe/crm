<template>
  <div class="space-y-6">
    <Section title="Rate Include">
      <div v-if="!includes.length" class="py-4 text-center text-sm text-ink-gray-5">
        No items
      </div>
      <table v-else class="w-full text-sm">
        <thead class="border-b border-outline-gray-2">
          <tr>
            <th class="pb-2 text-left font-medium text-ink-gray-7">Title</th>
            <th class="pb-2 text-left font-medium text-ink-gray-7">Item</th>
            <th class="pb-2 text-right font-medium text-ink-gray-7">Price</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in includes" :key="a.name" class="border-b border-outline-gray-1">
            <td class="py-2 text-ink-gray-7">{{ a.title }}</td>
            <td class="py-2 text-ink-gray-9">{{ a.item_name }}</td>
            <td class="py-2 text-right text-ink-gray-9">{{ formatCurrency(a.price) }}</td>
          </tr>
        </tbody>
      </table>
    </Section>

    <Section title="Rate Exclude">
      <div v-if="!excludes.length" class="py-4 text-center text-sm text-ink-gray-5">
        No items
      </div>
      <table v-else class="w-full text-sm">
        <thead class="border-b border-outline-gray-2">
          <tr>
            <th class="pb-2 text-left font-medium text-ink-gray-7">Title</th>
            <th class="pb-2 text-left font-medium text-ink-gray-7">Item</th>
            <th class="pb-2 text-right font-medium text-ink-gray-7">Price</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in excludes" :key="a.name" class="border-b border-outline-gray-1">
            <td class="py-2 text-ink-gray-7">{{ a.title }}</td>
            <td class="py-2 text-ink-gray-9">{{ a.item_name }}</td>
            <td class="py-2 text-right text-ink-gray-9">{{ formatCurrency(a.price) }}</td>
          </tr>
        </tbody>
      </table>
    </Section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Section from './shared/Section.vue'

const props = defineProps(['quotation'])
const doc = computed(() => props.quotation.doc)
const includes = computed(() => doc.value?.additionals?.filter(a => a.type === 'additional1') || [])
const excludes = computed(() => doc.value?.additionals?.filter(a => a.type === 'additional2') || [])

function formatCurrency(amount) {
  if (!amount) return '-'
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(amount)
}
</script>