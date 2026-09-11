<template>
  <Autocomplete
    v-if="options.length"
    :model-value="null"
    :options="options"
    :placeholder="__('Search fields')"
    @update:model-value="insert"
  >
    <template #target="{ togglePopover }">
      <Button
        variant="ghost"
        size="sm"
        icon-left="lucide-braces"
        :label="__('Insert field')"
        @click="togglePopover"
      />
    </template>
  </Autocomplete>
</template>

<script setup>
import { Autocomplete, Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['insert'])

/**
 * Params are rendered as templates, so a value can quote the record it acts on. Offering the
 * fields is the difference between "type {{ doc.first_name }}" and picking "First Name" -
 * and searchable, because a document type with sixty fields is not a list you scroll.
 */
const options = computed(() =>
  props.fields
    .filter((field) => field.fieldname)
    .map((field) => ({
      label: field.label || field.fieldname,
      description: field.fieldname,
      value: field.fieldname,
    })),
)

function insert(option) {
  if (option?.value) emit('insert', `{{ doc.${option.value} }}`)
}
</script>
