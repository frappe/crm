<template>
  <FormControl
    :type="show ? 'text' : 'password'"
    :value="modelValue || value"
    v-bind="$attrs"
    @keydown.meta.i.prevent="show = !show"
  >
    <template #prefix v-if="$slots.prefix">
      <slot name="prefix" />
    </template>
    <template #suffix>
      <FeatherIcon
        v-show="showEye"
        :name="show ? 'eye-off' : 'eye'"
        class="h-3 cursor-pointer mr-1"
        @click="show = !show"
      />
    </template>
  </FormControl>
</template>
<script setup>
import { FormControl } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  value: {
    type: [String, Number],
    default: '',
  },
})
const show = ref(false)
const showEye = computed(() => {
  let v = props.modelValue || props.value
  return !v?.includes('*')
})
</script>
