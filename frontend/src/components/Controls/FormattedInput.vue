<template>
  <FormControl
    :value="displayValue"
    @focus="isFocused = true"
    @blur="isFocused = false"
    v-bind="$attrs"
  />
</template>
<script setup>
import { FormControl } from 'frappe-ui'
import { ref, computed } from 'vue'

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

const isFocused = ref(false)

const displayValue = computed(() => {
  return isFocused.value ? props.value : props.formattedValue
})
</script>
