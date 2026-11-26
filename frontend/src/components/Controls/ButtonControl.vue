<template>
  <Button
    :label="__(label)"
    :theme="theme"
    :variant="variant"
    :icon-left="iconLeft"
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
import Icon from '@/components/Icon.vue'
import { Button } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  icon: { type: String, default: null },
  theme: { type: String, default: 'gray' },
  variant: { type: String, default: 'subtle' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])

// Tailwind only makes a lucide-* class for names written in the source, so runtime names use the sprite
const iconLeft = computed(
  () => props.icon && (() => h(Icon, { icon: props.icon })),
)
</script>
