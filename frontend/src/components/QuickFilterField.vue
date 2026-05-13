<template>
  <Checkbox
    v-if="filter.fieldtype == 'Check'"
    v-model="filter.value"
    :label="filter.label"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <Select
    v-else-if="filter.fieldtype === 'Select'"
    v-model="filter.value"
    class="w-full"
    :options="filter.options"
    :placeholder="filter.label"
    @update:modelValue="updateFilter(filter, $event)"
  />
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
  />
  <component
    :is="filter.fieldtype === 'Date' ? DatePicker : DateTimePicker"
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="border-none"
    :value="filter.value"
    :placeholder="filter.label"
    @change="(v) => updateFilter(filter, v)"
  />
  <TextInput
    v-else
    v-model="filter.value"
    :placeholder="filter.label"
    @input.stop="debouncedFn(filter, $event.target.value)"
  />
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import {
  TextInput,
  Select,
  Checkbox,
  DatePicker,
  DateTimePicker,
} from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { reactive, watch } from 'vue'

const props = defineProps({
  filter: { type: Object, required: true },
})

const filter = reactive(props.filter)

const emit = defineEmits(['applyQuickFilter'])

watch(
  () => props.filter,
  (newFilter) => Object.assign(filter, newFilter),
  { deep: true },
)

const debouncedFn = useDebounceFn((f, value) => {
  emit('applyQuickFilter', f, value)
}, 500)

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}
</script>
