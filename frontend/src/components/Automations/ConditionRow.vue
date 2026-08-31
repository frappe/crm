<template>
  <div class="grid grid-cols-3 gap-2">
    <FormControl
      v-model="condition.field"
      type="text"
      :placeholder="__('field, e.g. status')"
    />
    <FormControl
      v-model="condition.operator"
      type="select"
      :options="operatorOptions"
    />
    <FormControl
      v-model="condition.value"
      type="text"
      :placeholder="__('value')"
      :disabled="['is_set', 'is_not_set'].includes(condition.operator)"
    />
  </div>
</template>

<script setup>
import { FormControl } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps({
  meta: { type: Object, default: () => ({}) },
  required: { type: Boolean, default: false },
})

const model = defineModel({ type: Object, default: null })

// keep a stable object so the inputs always have something to bind to
const condition = computed(() => {
  if (!model.value) {
    model.value = { field: '', operator: 'equals', value: '' }
  }
  return model.value
})

const operatorOptions = computed(() =>
  (props.meta.data?.condition_operators || [
    'equals',
    'not_equals',
    'contains',
    'is_set',
    'is_not_set',
  ]).map((op) => ({ label: __(op), value: op })),
)

watch(
  () => condition.value.operator,
  (op) => {
    if (['is_set', 'is_not_set'].includes(op)) condition.value.value = ''
  },
)
</script>
