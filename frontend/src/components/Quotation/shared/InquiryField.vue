<template>
  <div>
    <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
      {{ label }}
    </label>
    <Autocomplete
      :modelValue="modelValue"
      :options="options"
      class="mt-1"
      :placeholder="__('Search won deal...')"
      @update:modelValue="onChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Autocomplete, createResource } from 'frappe-ui'

const props = defineProps({
  label: { type: String, default: 'Inquiry' },
  modelValue: String,
})

const emit = defineEmits(['update:modelValue', 'save', 'select'])  // ← tambah 'select'

const options = ref([])
const deals = ref([])  // ← simpan data deal lengkap

const resource = createResource({
  url: 'crm.api.quotation.get_available_inquiries',
  onSuccess(data) {
    deals.value = data  // ← simpan data lengkap
    options.value = data.map(d => ({
      label: `${d.name} — ${d.organization || ''}`,
      value: d.name,
    }))
  },
})

onMounted(() => {
  resource.submit()
})

function onChange(val) {
  const value = val?.value || val
  emit('update:modelValue', value)
  emit('save', value)

  // ← cari deal lengkap dan emit
  const selectedDeal = deals.value.find(d => d.name === value)
  if (selectedDeal) {
    emit('select', selectedDeal)
  }
}
</script>