<template>
  <FormControl
    v-if="filter.fieldtype == 'Check'"
    :label="filter.label"
    type="checkbox"
    v-model="filter.value"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <FormControl
    v-else-if="filter.fieldtype === 'Select'"
    class="form-control cursor-pointer [&_select]:cursor-pointer"
    type="select"
    v-model="filter.value"
    :options="filter.options"
    :placeholder="filter.label"
    @change.stop="updateFilter(filter, $event.target.value)"
  >
    <template #item-label="{ option }">
      {{ option.label || option.value }}
    </template>
  </FormControl>
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
  />
  <FormControl
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="form-control cursor-pointer [&_select]:cursor-pointer"
    type="select"
    v-model="filter.value"
    :options="filter.options || timespanOptions"
    :placeholder="filter.label"
    @change.stop="updateFilter(filter, $event.target.value)"
  >
    <template #item-label="{ option }">
      {{ option.label || option.value }}
    </template>
  </FormControl>
  <FormControl
    v-else
    v-model="filter.value"
    type="text"
    :placeholder="filter.label"
    @input.stop="debouncedFn(filter, $event.target.value)"
  />
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { timespanOptions } from '@/utils/timeOptions'
import { computed } from 'vue'

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['applyQuickFilter'])

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}

const debouncedFn = useDebounceFn((f, value) => {
  emit('applyQuickFilter', f, value)
}, 500)
</script>
