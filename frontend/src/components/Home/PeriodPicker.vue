<template>
  <Dropdown :options="options">
    <button
      type="button"
      class="flex items-center gap-0.5 text-ink-gray-5 hover:text-ink-gray-7"
    >
      {{ labels[current] }}
      <span class="lucide-chevron-down size-3" aria-hidden="true" />
    </button>
  </Dropdown>
</template>
<script setup>
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  period: { type: String, default: 'last_month' },
})

const emit = defineEmits(['change'])

const current = computed(() => props.period || 'last_month')

// Keys match PERIOD_DAYS in home_layout.py.
const labels = {
  last_week: __('Last week'),
  last_month: __('Last month'),
  last_3_months: __('Last 3 months'),
}

const options = computed(() => [
  {
    group: __('Period'),
    hideLabel: true,
    options: Object.entries(labels).map(([period, label]) => ({
      label,
      selected: period === current.value,
      onClick: () => period !== current.value && emit('change', period),
    })),
  },
])
</script>
