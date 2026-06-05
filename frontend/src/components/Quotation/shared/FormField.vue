<template>
  <div>
    <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
      {{ label }} <span v-if="required" class="text-ink-red-4">*</span>
    </label>

    <!-- Readonly display -->
    <div
      v-if="readonly"
      class="mt-1 w-full rounded border border-outline-gray-2 bg-surface-gray-2 px-2 py-1.5 text-sm text-ink-gray-7"
    >
      {{ modelValue || '-' }}
    </div>

    <select
      v-else-if="type === 'select'"
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      class="mt-1 w-full rounded border border-outline-gray-2 px-2 py-1.5 text-sm"
    >
      <option v-for="opt in options" :key="opt" :value="opt">{{ opt }}</option>
    </select>

    <textarea
      v-else-if="type === 'textarea'"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      class="mt-1 w-full rounded border border-outline-gray-2 px-2 py-1.5 text-sm"
      rows="3"
    />

    <Autocomplete
      v-else-if="type === 'link'"
      :modelValue="modelValue"
      :options="linkOptions"
      class="mt-1"
      @update:modelValue="(v) => $emit('update:modelValue', v?.value || v)"
    />

    <input
      v-else
      :type="type === 'number' ? 'number' : type === 'date' ? 'date' : 'text'"
      :value="modelValue"
      @input="$emit('update:modelValue', type === 'number' ? Number($event.target.value) : $event.target.value)"
      class="mt-1 w-full rounded border border-outline-gray-2 px-2 py-1.5 text-sm"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Autocomplete, createResource } from 'frappe-ui'

const props = defineProps({
  label: String,
  modelValue: [String, Number],
  type: { type: String, default: 'text' },
  options: Array,
  doctype: String,
  required: Boolean,
  readonly: Boolean,
})

defineEmits(['update:modelValue'])

const linkOptions = ref([])

if (props.type === 'link' && props.doctype && !props.readonly) {
  createResource({
    url: 'frappe.client.get_list',
    params: { doctype: props.doctype, fields: ['name'], limit_page_length: 50 },
    auto: true,
    onSuccess(data) {
      linkOptions.value = data.map(d => ({ label: d.name, value: d.name }))
    },
  })
}
</script>