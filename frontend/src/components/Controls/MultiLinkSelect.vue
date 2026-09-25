<template>
  <MultiSelect
    :model-value="modelValue"
    variant="outline"
    :options="options"
    :loading="loading"
    :filterable="false"
    :placeholder="placeholder"
    :empty-text="__('No results found')"
    @update:model-value="$emit('update:modelValue', $event)"
    @update:query="query = $event"
  />
</template>

<script setup>
import { MultiSelect, call } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { computed, ref, watch } from 'vue'

// Several values of one doctype, searched like Link.vue (search_link).
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  doctype: { type: String, required: true },
  filters: { type: [Array, Object], default: null },
  placeholder: { type: String, default: '' },
})

defineEmits(['update:modelValue'])

const query = ref('')
const loading = ref(false)
const fetchedOptions = ref([])
let requestId = 0

// keep selected values listed even when the current search doesn't return them
const options = computed(() => {
  const values = new Map(
    props.modelValue.map((value) => [value, { label: value, value }]),
  )
  fetchedOptions.value.forEach((option) => values.set(option.value, option))
  return [...values.values()]
})

watchDebounced(query, search, { debounce: 250, immediate: true })
watch(
  () => [props.doctype, props.filters],
  () => search(query.value),
)

async function search(txt) {
  const currentRequest = ++requestId
  loading.value = true
  try {
    const results = await call('frappe.desk.search.search_link', {
      doctype: props.doctype,
      txt: txt || '',
      filters: props.filters,
    })
    if (currentRequest === requestId) {
      fetchedOptions.value = results.map((r) => ({
        label: r.label || r.value,
        value: r.value,
      }))
    }
  } catch (error) {
    console.error('Unable to search', props.doctype, error)
    if (currentRequest === requestId) fetchedOptions.value = []
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}
</script>
