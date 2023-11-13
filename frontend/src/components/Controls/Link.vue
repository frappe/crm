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
    >
      <template #target="{ open, togglePopover }">
        <slot name="target" v-bind="{ open, togglePopover }" />
      </template>

      <template #prefix>
        <slot name="prefix" />
      </template>

      <template #item-prefix="{ active, selected, option }">
        <slot name="item-prefix" v-bind="{ active, selected, option }" />
      </template>

      <template v-if="$slots.footer" #footer="{ value, close }">
        <slot name="footer" v-bind="{ value, close }" />
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import { call } from 'frappe-ui'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { useAttrs, computed, ref } from 'vue'
import { computedAsync, watchDebounced, useStorage } from '@vueuse/core'

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
const text = ref('')

watchDebounced(
  () => autocomplete.value?.query,
  (val) => (text.value = val),
  { debounce: 500 }
)

const options = computedAsync(async () => {
  let cachedOptions = localStorage.getItem(props.doctype + '-' + text.value)

  if (cachedOptions) {
    return JSON.parse(cachedOptions)
  }

  let options = await call('frappe.desk.search.search_link', {
    txt: text.value,
    doctype: props.doctype,
  })
  options = options?.map((option) => {
    return {
      label: option.value,
      value: option.value,
    }
  })

  useStorage(props.doctype + '-' + text.value, options)

  return options
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
