<template>
  <FormControl
    :type="show ? 'text' : 'password'"
    :value="modelValue || value"
    v-bind="$attrs"
  >
    <template #suffix>
      <Button v-show="showEye" class="!h-4" @click="show = !show">
        <FeatherIcon :name="show ? 'eye-off' : 'eye'" class="h-3" />
      </Button>
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
