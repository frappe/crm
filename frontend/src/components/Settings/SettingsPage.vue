<template>
  <div class="flex h-full flex-col gap-8">
    <h2 class="text-xl font-semibold leading-none">
      {{ __(doctype) }}
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

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.doctype,
  fields: ['*'],
  cache: props.doctype,
  auto: true,
})

const sections = computed(() => {
  if (!fields.data) return []
  let _sections = []
  let fieldsData = fields.data

  if (fieldsData[0].type !== 'Section Break') {
    _sections.push({
      label: 'General',
      columns: 1,
      fields: [],
    })
  }
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
