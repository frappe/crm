<template>
  <Dropdown :options="options">
    <Button
      v-if="button"
      variant="outline"
      :label="labels[current]"
      iconRight="lucide-chevron-down"
    />
    <button
      v-else
      type="button"
      class="flex items-center gap-0.5 text-ink-gray-7 hover:text-ink-gray-9"
    >
      {{ labels[current] }}
      <span class="lucide-chevron-down size-3" aria-hidden="true" />
    </button>
  </Dropdown>
</template>
<script setup>
import { Button, Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  period: { type: String, default: 'last_month' },
  labels: { type: Object, default: null },
  // A picker on its own in a widget header is a button; one inside a sentence stays text
  button: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])

const current = computed(() => props.period || 'last_month')

// Keys match PERIOD_DAYS in home_layout.py.
const defaultLabels = {
  last_week: __('Last week'),
  last_month: __('Last month'),
  last_3_months: __('Last 3 months'),
}

const labels = computed(() => props.labels || defaultLabels)

const options = computed(() => [
  {
    group: __('Period'),
    hideLabel: true,
    options: Object.entries(labels.value).map(([period, label]) => ({
      label,
      selected: period === current.value,
      onClick: () => period !== current.value && emit('change', period),
    })),
  },
])
</script>
