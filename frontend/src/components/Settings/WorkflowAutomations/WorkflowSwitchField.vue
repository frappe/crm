<template>
  <div class="flex items-center justify-between gap-3">
    <div class="text-sm text-ink-gray-7">{{ label }}</div>
    <Switch
      size="sm"
      :model-value="Boolean(modelValue)"
      @update:model-value="$emit('update:modelValue', $event ? 1 : 0)"
    />
  </div>
</template>

<script setup>
import { Switch } from 'frappe-ui'

defineProps({
  label: { type: String, required: true },
  modelValue: { type: [Boolean, Number], default: 0 },
})

defineEmits(['update:modelValue'])
</script>
