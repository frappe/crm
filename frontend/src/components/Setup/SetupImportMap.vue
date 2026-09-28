<template>
  <div class="flex flex-col gap-4">
    <p class="text-p-base text-ink-gray-6">
      {{ __('Match each column in your file to a lead field.') }}
    </p>
    <div class="rounded-md border border-outline-gray-2">
      <div
        class="grid grid-cols-2 gap-4 border-b border-outline-gray-2 px-4 py-2 text-sm text-ink-gray-5"
      >
        <div>{{ __('Column in file') }}</div>
        <div>{{ __('Lead field') }}</div>
      </div>
      <div class="max-h-[300px] overflow-y-auto">
        <div
          v-for="mapping in mappings"
          :key="mapping.index"
          class="grid grid-cols-2 items-center gap-4 px-4 py-2"
        >
          <div class="min-w-0">
            <div class="truncate text-base text-ink-gray-8">
              {{ mapping.header }}
            </div>
            <div class="truncate text-sm text-ink-gray-5">
              {{ sampleValue(mapping.index) }}
            </div>
          </div>
          <FormControl
            v-model="mapping.fieldname"
            type="select"
            :options="fieldOptions"
            :aria-label="__('Lead field for {0}', [mapping.header])"
          />
        </div>
      </div>
    </div>
    <ErrorMessage
      v-if="!nameMapped"
      :message="__('Map a column to First Name to continue.')"
    />
    <p
      v-else-if="unmappedRequired.length"
      class="rounded-md bg-surface-amber-2 p-2 text-sm text-ink-amber-6"
    >
      {{
        __('Required fields not mapped: {0}. Rows without them may fail.', [
          unmappedRequired.map((f) => __(f.label)).join(', '),
        ])
      }}
    </p>
    <div class="mt-auto flex justify-between">
      <Button :label="__('Back')" @click="emit('back')" />
      <Button
        variant="solid"
        :label="__('Continue')"
        :disabled="!nameMapped"
        :loading="saving"
        @click="emit('continue', mappings)"
      />
    </div>
  </div>
</template>

<script setup>
import { getMeta } from '@/stores/meta'
import {
  getColumnMappings,
  getUnmappedRequiredFields,
  isLeadNameMapped,
} from '@/utils/setup'
import { Button, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  preview: { type: Object, required: true },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['back', 'continue'])

const UNSUPPORTED_TYPES = [
  'Table',
  'Table MultiSelect',
  'Attach',
  'Attach Image',
]
// Filled in by the lead controller when missing.
const CONTROLLER_SET_FIELDS = ['status', 'naming_series']

const { getFields } = getMeta('CRM Lead')
const mappings = ref(getColumnMappings(props.preview))

const leadFields = computed(() =>
  getFields().filter(
    (f) => !f.read_only && !UNSUPPORTED_TYPES.includes(f.fieldtype),
  ),
)

const fieldOptions = computed(() => [
  { label: __("Don't import"), value: '' },
  ...leadFields.value.map((f) => ({ label: __(f.label), value: f.fieldname })),
])

const nameMapped = computed(() => isLeadNameMapped(mappings.value))

const unmappedRequired = computed(() =>
  getUnmappedRequiredFields(
    leadFields.value.filter(
      (f) => !CONTROLLER_SET_FIELDS.includes(f.fieldname),
    ),
    mappings.value,
  ),
)

function sampleValue(index) {
  const row = props.preview.data?.find((r) => r[index + 1])
  return row ? String(row[index + 1]) : ''
}
</script>
