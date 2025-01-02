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
      <ErrorMessage class="mt-2" :message="error" />
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <Spinner class="size-8" />
    </div>
    <div class="flex flex-row-reverse">
      <Button
        :loading="data.save.loading"
        :label="__('Update')"
        variant="solid"
        @click="update"
      />
    </div>
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout.vue'
import {
  createDocumentResource,
  createResource,
  Spinner,
  Badge,
  ErrorMessage,
} from 'frappe-ui'
import { createToast, getRandom } from '@/utils'
import { ref, computed } from 'vue'

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

const error = ref(null)

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.doctype,
  fields: ['*'],
  auto: true,
  setValue: {
    onSuccess: () => {
      error.value = null
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

function update() {
  error.value = null
  if (validateMandatoryFields()) return
  data.save.submit()
}

function validateMandatoryFields() {
  if (!tabs.value) return false
  for (let section of tabs.value[0].sections) {
    for (let column of section.columns) {
      for (let field of column.fields) {
        if (
          (field.mandatory ||
            (field.mandatory_depends_on && field.mandatory_via_depends_on)) &&
          !data.doc[field.name]
        ) {
          error.value = __('{0} is mandatory', [__(field.label)])
          return true
        }
      }
    }
  }
  return false
}
</script>
