<template>
  <TextInput
    ref="inputRef"
    v-model="displayValue"
    v-bind="$attrs"
    @focus="handleFocus"
    @blur="isFocused = false"
  />
</template>
<script setup>
import { TextInput } from 'frappe-ui'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  value: { type: [String, Number], default: '' },
  formattedValue: { type: [String, Number], default: '' },
})

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
</script>
