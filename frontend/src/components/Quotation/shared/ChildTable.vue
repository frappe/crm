<template>
  <div v-if="!rows.length" class="py-4 text-center text-sm text-ink-gray-5">
    No items
  </div>

  <table v-else class="w-full text-sm">
    <thead class="border-b border-outline-gray-2">
      <tr>
        <th
          v-for="col in columns"
          :key="col.fieldname"
          class="pb-2 px-2 font-medium text-ink-gray-7"
          :class="col.align === 'right' ? 'text-right' : 'text-left'"
        >
          {{ col.label }}
        </th>
        <th class="w-8"></th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="(row, idx) in rows"
        :key="idx"
        class="border-b border-outline-gray-1"
      >
        <td
          v-for="col in columns"
          :key="col.fieldname"
          class="px-2 py-2"
          :class="col.align === 'right' ? 'text-right' : 'text-left'"
        >
          <!-- Readonly -->
          <span v-if="col.readonly">{{ formatVal(row[col.fieldname], col.type) }}</span>

          <!-- Select -->
          <select
            v-else-if="col.type === 'select'"
            :value="row[col.fieldname]"
            @change="$emit('update', idx, col.fieldname, $event.target.value)"
            class="w-full rounded border-0 bg-transparent px-1 py-1 text-sm focus:bg-surface-gray-1 focus:outline-none"
          >
            <option v-for="opt in col.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <!-- Number / Currency -->
          <input
            v-else-if="col.type === 'number' || col.type === 'currency'"
            type="number"
            :value="row[col.fieldname]"
            @blur="$emit('update', idx, col.fieldname, Number($event.target.value))"
            class="w-full rounded border-0 bg-transparent px-1 py-1 text-sm focus:bg-surface-gray-1 focus:outline-none"
            :class="col.align === 'right' ? 'text-right' : ''"
          />

          <!-- Text -->
          <input
            v-else
            type="text"
            :value="row[col.fieldname]"
            @blur="$emit('update', idx, col.fieldname, $event.target.value)"
            class="w-full rounded border-0 bg-transparent px-1 py-1 text-sm focus:bg-surface-gray-1 focus:outline-none"
          />
        </td>
        <td class="px-2 py-2">
          <button
            @click="$emit('remove', idx)"
            class="text-ink-red-4 hover:text-ink-red-5"
            title="Remove"
          >
            <FeatherIcon name="trash-2" class="h-4 w-4" />
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({
  rows: Array,
  columns: Array,
})

defineEmits(['update', 'remove'])

function formatVal(val, type) {
  if (val == null) return '-'
  if (type === 'currency') {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0,
    }).format(val)
  }
  return val
}
</script>