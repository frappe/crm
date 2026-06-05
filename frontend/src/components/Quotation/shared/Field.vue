<template>
  <div>
    <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
      {{ label }}
    </label>
    <p
      class="mt-1 text-sm text-ink-gray-9"
      :class="{ 'whitespace-pre-wrap': multiline }"
    >
      {{ displayValue }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { default: null },
  multiline: { type: Boolean, default: false },
  format: { type: String, default: 'text' }, // text, currency, date
})

const displayValue = computed(() => {
  if (props.value == null || props.value === '') return '-'
  if (props.format === 'currency') {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(props.value)
  }
  if (props.format === 'date') {
    return new Date(props.value).toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' })
  }
  return props.value
})
</script>