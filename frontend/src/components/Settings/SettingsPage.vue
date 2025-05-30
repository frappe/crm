<template>
  <div class="flex h-full flex-col gap-8">
    <h2
      class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-9"
    >
      <div>{{ title || __(doctype) }}</div>
      <Badge
        v-if="data.isDirty"
        :label="__('Not Saved')"
        variant="subtle"
        theme="orange"
      />
    </h2>
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
    <div class="flex justify-between gap-2">
      <div>
        <ErrorMessage class="mt-2" :message="data.save.error" />
      </div>
      <Button
        :loading="data.save.loading"
        :label="__('Update')"
        variant="solid"
        @click="data.save.submit()"
      />
    </div>
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  createDocumentResource,
  createResource,
  Spinner,
  Badge,
  ErrorMessage,
} from 'frappe-ui'
import { createToast, getRandom } from '@/utils'
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
      createToast({
        title: __('Success'),
        text: __(props.successMessage),
        icon: 'check',
        iconClasses: 'text-ink-green-3',
      })
    },
    onError: (err) => {
      createToast({
        title: __('Error'),
        text: err.message + ': ' + err.messages[0],
        icon: 'x',
        iconClasses: 'text-ink-red-4',
      })
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
