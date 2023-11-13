<template>
  <div class="space-y-1.5">
    <label class="block" :class="labelClasses" v-if="attrs.label">
      {{ attrs.label }}
    </label>
    <Autocomplete
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
import { defineModel, useAttrs, computed } from 'vue'
import { computedAsync } from '@vueuse/core'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const value = defineModel()
const attrs = useAttrs()

const options = computedAsync(async () => {
  let options = await call('frappe.desk.search.search_link', {
    txt: '',
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
