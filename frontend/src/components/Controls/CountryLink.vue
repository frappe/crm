<template>
  <Link
    v-bind="$attrs"
    :doctype="doctype"
    :value="value"
    @change="handleChange"
  >
    <template #item-label="{ option }">
      <div class="cursor-pointer">
        {{ __(option.value) }}
      </div>
    </template>
    <template #selected-option="{ option }">
      {{ __(option.value) }}
    </template>
  </Link>
</template>

<script setup>
import Link from './Link.vue'
import { computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'Country'
  },
  modelValue: {
    type: [String, Object],
    default: ''
  }
})

const emit = defineEmits(['change', 'update:modelValue'])

const value = computed(() => {
  if (!props.modelValue) return ''
  if (typeof props.modelValue === 'string') return props.modelValue
  return props.modelValue.country || ''
})

function handleChange(val) {
  console.log('Country selected:', val)
  emit('change', val)
  emit('update:modelValue', val)
}
</script> 