<!-- Searches the DocTypes the user can read that have a list to open. -->
<template>
  <Combobox
    :model-value="modelValue"
    :options="options"
    :label="label"
    :placeholder="__('Search DocTypes you can read')"
    :error="error || undefined"
    :loading="loading"
    :filterable="false"
    @update:query="search"
    @update:model-value="(value) => emit('update:modelValue', value)"
    @focus="search('')"
  >
    <template #prefix>
      <span class="lucide-table size-4 text-ink-gray-6" aria-hidden="true" />
    </template>
  </Combobox>
</template>

<script setup>
import { searchDoctypes } from './editor'
import { Combobox, debounce } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: null },
  label: { type: String, default: '' },
  error: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue'])

const found = ref([])
const loading = ref(false)

const options = computed(() => {
  const names = new Set(found.value)
  if (props.modelValue) names.add(props.modelValue)
  return [...names].map((name) => ({ label: name, value: name }))
})

const search = debounce(async (txt) => {
  loading.value = true
  try {
    found.value = await searchDoctypes(txt || '')
  } finally {
    loading.value = false
  }
}, 200)
</script>
