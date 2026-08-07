<template>
  <div class="fc-finance-table">
    <!-- Loading state -->
    <div v-if="loading" class="space-y-2">
      <div v-for="n in 5" :key="n" class="h-12 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-sm text-red-500 py-4">
      Failed to load data. <button class="underline" @click="$emit('retry')">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!rows || !rows.length" class="text-center py-10 text-sm text-gray-400">
      {{ emptyLabel || 'No records found.' }}
    </div>

    <!-- Desktop table -->
    <div v-else-if="!isMobile" class="overflow-x-auto rounded border border-gray-200 dark:border-gray-700">
      <table class="w-full text-sm">
        <thead class="sticky top-0 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-3 py-2.5 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide whitespace-nowrap',
                col.align === 'right' ? 'text-right' : '',
              ]"
            >{{ col.label }}</th>
            <th v-if="$slots.actions" class="px-3 py-2.5 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr
            v-for="row in rows"
            :key="row.name"
            class="hover:bg-gray-50 dark:hover:bg-gray-800/60 cursor-pointer transition-colors"
            @click="$emit('row-click', row)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-3 py-2.5 text-gray-700 dark:text-gray-300',
                col.align === 'right' ? 'text-right' : '',
              ]"
            >
              <StatusPill v-if="col.type === 'status'" :status="row[col.key]" />
              <span v-else-if="col.type === 'currency'" class="font-medium">
                {{ formatCurrency(row[col.key], row.currency) }}
              </span>
              <span v-else-if="col.type === 'date'" class="text-xs">{{ row[col.key] || '—' }}</span>
              <span v-else>{{ row[col.key] ?? '—' }}</span>
            </td>
            <td v-if="$slots.actions" class="px-3 py-2.5 text-right">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile card layout -->
    <div v-else class="space-y-3">
      <div
        v-for="row in rows"
        :key="row.name"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 shadow-sm cursor-pointer"
        @click="$emit('row-click', row)"
      >
        <div class="flex items-start justify-between gap-2 mb-2">
          <div>
            <p class="font-medium text-gray-800 dark:text-gray-200 text-sm">
              {{ row[columns[0]?.key] || row.name }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ row[columns[1]?.key] }}
            </p>
          </div>
          <div class="text-right flex-shrink-0">
            <p v-if="amountCol" class="font-semibold text-gray-700 dark:text-gray-300 text-sm">
              {{ formatCurrency(row[amountCol.key], row.currency) }}
            </p>
            <StatusPill v-if="statusCol" :status="row[statusCol.key]" />
          </div>
        </div>
        <div v-if="$slots.actions" class="mt-2 flex flex-col gap-1.5">
          <slot name="actions" :row="row" />
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="rows && rows.length && (rows.length === pageSize || page > 0)" class="flex items-center justify-end gap-2 mt-3">
      <button
        :disabled="page <= 0"
        class="px-3 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click="$emit('update:page', page - 1)"
      >Previous</button>
      <span class="text-xs text-gray-500">Page {{ page + 1 }}</span>
      <button
        :disabled="rows.length < pageSize"
        class="px-3 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click="$emit('update:page', page + 1)"
      >Next</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StatusPill from './StatusPill.vue'
import { useBreakpoint } from '../composables/useBreakpoint.js'
import { useCurrency } from '../composables/useCurrency.js'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: Object, default: null },
  emptyLabel: { type: String, default: '' },
  page: { type: Number, default: 0 },
  pageSize: { type: Number, default: 20 },
})

defineEmits(['row-click', 'retry', 'update:page'])

const { isMobile } = useBreakpoint()
const { formatCurrency } = useCurrency()

const amountCol = computed(() => props.columns.find(c => c.type === 'currency'))
const statusCol = computed(() => props.columns.find(c => c.type === 'status'))
</script>
