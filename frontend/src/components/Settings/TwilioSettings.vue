<template>
  <div class="flex flex-col gap-8 h-full">
    <h2 class="text-xl font-semibold leading-none">
      {{ __('Twilio Settings') }}
    </h2>
    <div class="flex-1 overflow-y-auto">
      <Fields
        v-if="data?.doc && sections"
        :sections="sections"
        :data="data.doc"
      />
    </div>
    <div class="flex flex-row-reverse">
      <Button :label="__('Update')" variant="solid" />
    </div>
  </div>
</template>
<script setup>
import Fields from '@/components/Fields.vue'
import { createDocumentResource, createResource } from 'frappe-ui'
import { computed } from 'vue'

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', 'Twilio Settings'],
  params: {
    doctype: 'Twilio Settings',
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const data = createDocumentResource({
  doctype: 'Twilio Settings',
  name: 'Twilio Settings',
  fields: ['*'],
  cache: 'Twilio Settings',
  auto: true,
})

const sections = computed(() => {
  if (!fields.data) return []
  let _sections = []
  let fieldsData = fields.data

  fieldsData.forEach((field) => {
    if (field.type === 'Section Break') {
      _sections.push({
        label: field.value,
        columns: 1,
        fields: [],
      })
    } else if (field.type === 'Column Break') {
      _sections[_sections.length - 1].columns += 1
    } else {
      _sections[_sections.length - 1].fields.push({
        ...field,
        name: field.value,
      })
    }
  })

  return _sections
})
</script>
