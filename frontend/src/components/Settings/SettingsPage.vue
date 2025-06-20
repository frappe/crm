<template>
  <div class="flex h-full flex-col gap-6">
    <div class="flex justify-between">
      <div class="flex flex-col gap-1 w-9/12">
        <h2
          class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-8"
        >
          {{ title || __(doctype) }}
          <Badge
            v-if="data.isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :loading="data.save.loading"
          :label="__('Update')"
          variant="solid"
          @click="data.save.submit()"
        />
      </div>
    </div>
    <div v-if="!data.get.loading" class="flex-1 overflow-y-auto">
      <FieldLayout
        v-if="data?.doc && tabs"
        :tabs="tabs"
        :data="data.doc"
        :doctype="doctype"
      />
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <Spinner class="size-8" />
    </div>
    <ErrorMessage :message="data.save.error" />
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  createDocumentResource,
  createResource,
  Spinner,
  Badge,
  toast,
  ErrorMessage,
} from 'frappe-ui'
import { getRandom } from '@/utils'
import { computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: '',
  },
  successMessage: {
    type: String,
    default: 'Updated Successfully',
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
  auto: true,
  setValue: {
    onSuccess: () => {
      toast.success(__(props.successMessage))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  },
})

const tabs = computed(() => {
  if (!fields.data) return []
  let _tabs = []
  let fieldsData = fields.data

  if (fieldsData[0].type != 'Tab Break') {
    let _sections = []
    if (fieldsData[0].type != 'Section Break') {
      _sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    _tabs.push({ name: 'first_tab', sections: _sections })
  }

  fieldsData.forEach((field) => {
    let last_tab = _tabs[_tabs.length - 1]
    let _sections = _tabs.length ? last_tab.sections : []
    if (field.fieldtype === 'Tab Break') {
      _tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: 'section_' + getRandom(),
            columns: [{ name: 'column_' + getRandom(), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      _sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: 'column_' + getRandom(), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      _sections[_sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      let last_section = _sections[_sections.length - 1]
      let last_column = last_section.columns[last_section.columns.length - 1]
      last_column.fields.push(field)
    }
  })

  return _tabs
})
</script>
