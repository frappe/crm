<template>
  <div class="space-y-4">
    <template v-if="doc.trigger_type === 'Field Value Changed'">
      <FormControl
        v-model="doc.trigger_field"
        type="select"
        :label="__('Trigger Field')"
        :options="fieldOptions"
      />
      <FormControl v-model="doc.from_value" :label="__('From Value')" />
      <FormControl v-model="doc.to_value" :label="__('To Value')" />
    </template>
    <template v-else-if="doc.trigger_type === 'Scheduled'">
      <FormControl
        v-model="doc.cron_expression"
        :label="__('Cron Expression')"
        placeholder="0 9 * * *"
      />
    </template>
    <template v-else-if="doc.trigger_type === 'Date Based'">
      <FormControl
        v-model="doc.date_field"
        type="select"
        :label="__('Date Field')"
        :options="dateFieldOptions"
      />
      <FormControl
        v-model="doc.date_offset"
        type="number"
        :label="__('Date Offset')"
      />
      <FormControl
        v-model="doc.date_direction"
        type="select"
        :label="__('Date Direction')"
        :options="['Before', 'After']"
      />
    </template>
    <!-- Only for an event the trigger list does not already name. -->
    <template v-else-if="doc.trigger_type === 'Custom Event' && !isNamedEvent">
      <FormControl
        v-model="doc.custom_event"
        type="select"
        :label="__('Custom Event')"
        :options="events"
      />
    </template>
  </div>
</template>

<script setup>
import { eventTriggers, triggerValue } from './workflowTriggers'
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doc: { type: Object, required: true },
  fields: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
})

const isNamedEvent = computed(() =>
  eventTriggers(props.doc.document_type).some(
    (trigger) => trigger.value === triggerValue(props.doc),
  ),
)

const fieldOptions = computed(() => {
  return props.fields.map((field) => ({
    label: field.label || field.fieldname,
    value: field.fieldname,
  }))
})

const dateFieldOptions = computed(() => {
  return props.fields
    .filter((field) => ['Date', 'Datetime'].includes(field.fieldtype))
    .map((field) => ({
      label: field.label || field.fieldname,
      value: field.fieldname,
    }))
})
</script>
