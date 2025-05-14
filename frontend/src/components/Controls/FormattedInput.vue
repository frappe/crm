<template>
  <TextInput
    ref="inputRef"
    :value="displayValue"
    @focus="handleFocus"
    @blur="isFocused = false"
    v-bind="$attrs"
  />
  <slot name="description">
    <p v-if="attrs.description" class="mt-1.5" :class="descriptionClasses">
      {{ attrs.description }}
    </p>
  </slot>
</template>
<script setup>
import { TextInput } from 'frappe-ui'
import { ref, computed, nextTick, useAttrs } from 'vue'

const props = defineProps({
  value: {
    type: [String, Number],
    default: '',
  },
  formattedValue: {
    type: [String, Number],
    default: '',
  },
})

const attrs = useAttrs()

const isFocused = ref(false)
const inputRef = ref(null)

function handleFocus() {
  isFocused.value = true

  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.el?.select()
    }
  })
}

const displayValue = computed(() => {
  return isFocused.value ? props.value : props.formattedValue || props.value
})

const descriptionClasses = computed(() => {
  return [
    {
      sm: 'text-xs',
      md: 'text-base',
    }[attrs.size || 'sm'],
    'text-ink-gray-5',
  ]
})
</script>
