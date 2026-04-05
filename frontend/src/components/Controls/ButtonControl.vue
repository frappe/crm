<template>
  <Button
    :label="__(label)"
    :theme="theme"
    :variant="variant"
    :icon-left="icon"
    :disabled="disabled"
    v-bind="$attrs"
    @click.stop="emit('click', $event)"
  />
</template>
<script>
export function getButtonTheme(buttonColor) {
  const themeMap = {
    Primary: 'gray',
    Info: 'blue',
    Success: 'green',
    Warning: 'gray',
    Danger: 'red',
  }
  return themeMap[buttonColor] || 'gray'
}

export function getButtonVariant(buttonColor) {
  const variantMap = {
    Primary: 'solid',
    Info: 'subtle',
    Success: 'solid',
    Warning: 'subtle',
    Danger: 'solid',
  }
  return variantMap[buttonColor] || 'subtle'
}
</script>

<script setup>
import { Button } from 'frappe-ui'

defineProps({
  label: { type: String, required: true },
  icon: { type: String, default: null },
  theme: { type: String, default: 'gray' },
  variant: { type: String, default: 'subtle' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])
</script>
