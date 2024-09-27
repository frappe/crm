<template>
  <div class="flex h-full flex-col gap-8">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
      <div>{{ title || __(doctype) }}</div>
      <Badge
        v-if="data.isDirty"
        :label="__('Not Saved')"
        variant="subtle"
        theme="orange"
      />
    </h2>
    <div v-if="!data.get.loading" class="flex-1 overflow-y-auto">
      <Fields
        v-if="data?.doc && sections"
        :sections="sections"
        :data="data.doc"
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
import Fields from '@/components/Fields.vue'
import {
  createDocumentResource,
  createResource,
  Spinner,
  Badge,
  ErrorMessage,
} from 'frappe-ui'
import { evaluateDependsOnValue, createToast } from '@/utils'
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
  cache: props.doctype,
  auto: true,
  setValue: {
    onSuccess: () => {
      error.value = null
      createToast({
        title: __('Success'),
        text: __(props.successMessage),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: __('Error'),
        text: err.message + ': ' + err.messages[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  },
})

const sections = computed(() => {
  if (!fields.data) return []
  let _sections = []
  let fieldsData = fields.data

  if (fieldsData[0].type !== 'Section Break') {
    _sections.push({
      label: 'General',
      hideLabel: true,
      columns: 1,
      fields: [],
    })
  }
  fieldsData.forEach((field) => {
    if (field.type === 'Section Break') {
      _sections.push({
        label: field.value,
        hideLabel: true,
        columns: 1,
        fields: [],
      })
    } else if (field.type === 'Column Break') {
      _sections[_sections.length - 1].columns += 1
    } else {
      _sections[_sections.length - 1].fields.push({
        ...field,
        filters: field.link_filters && JSON.parse(field.link_filters),
        display_via_depends_on: evaluateDependsOnValue(
          field.depends_on,
          data.doc,
        ),
        mandatory_via_depends_on: evaluateDependsOnValue(
          field.mandatory_depends_on,
          data.doc,
        ),
        name: field.value,
      })
    }
  })

  return _sections
})

function update() {
  error.value = null
  if (validateMandatoryFields()) return
  data.save.submit()
}

function validateMandatoryFields() {
  for (let section of sections.value) {
    for (let field of section.fields) {
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
  return false
}
</script>
