<template>
  <div class="space-y-1.5">
    <label class="block" :class="labelClasses" v-if="attrs.label">
      {{ attrs.label }}
    </label>
    <Autocomplete
      ref="autocomplete"
      :options="options"
      v-model="value"
      :size="attrs.size || 'sm'"
      :variant="attrs.variant"
      :placeholder="attrs.placeholder"
    />
  </div>
</template>

<script setup>
import { call } from 'frappe-ui'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { useAttrs, computed, ref } from 'vue'
import { computedAsync } from '@vueuse/core'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const attrs = useAttrs()

const valuePropPassed = computed(() => 'value' in attrs)

const value = computed({
  get: () => (valuePropPassed.value ? attrs.value : props.modelValue),
  set: (val) =>
    emit(valuePropPassed.value ? 'change' : 'update:modelValue', val?.value),
})

const autocomplete = ref(null)
const text = computed(() => autocomplete.value?.query)

const options = computedAsync(async () => {
  let options = await call('frappe.desk.search.search_link', {
    txt: text.value || '',
    doctype: props.doctype,
  })
  return options?.map((option) => {
    return {
      label: option.value,
      value: option.value,
    }
  })
})

const labelClasses = computed(() => {
  return [
    {
      sm: 'text-xs',
      md: 'text-base',
    }[attrs.size || 'sm'],
    'text-gray-600',
  ]
})
</script>
