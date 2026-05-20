<template>
  <Rating
    :modelValue="(Number(modelValue) || 0) * starCount"
    :max="starCount"
    :step="0.5"
    :readonly="disabled"
    allow-clear
    show-value-tooltip
    :placement="placement"
    v-bind="$attrs"
    @update:modelValue="emit('update:modelValue', $event / starCount)"
  />
</template>

<script setup>
import { computed } from 'vue'
import { Rating } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Number, default: 0 },
  max: { type: [Number, String], default: 5 },
  disabled: { type: Boolean, default: false },
  placement: { type: String, default: 'right' },
})

const emit = defineEmits(['update:modelValue'])

// CRM backend persists rating as a 0-1 fraction; the library Rating uses star
// units. This wrapper is the boundary that converts between the two.
const starCount = computed(() => Number(props.max) || 5)
</script>
