<template>
  <div
    class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-gray-800">
      {{ __('Data') }}
      <Badge
        v-if="data.isDirty"
        class="ml-3"
        :label="'Not Saved'"
        theme="orange"
      />
    </div>
    <Button
      label="Save"
      variant="solid"
      :loading="data.save.loading"
      @click="saveChanges"
    />
  </div>
  <div
    v-if="data.get.loading"
    class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
  >
    <LoadingIndicator class="h-6 w-6" />
    <span>{{ __('Loading...') }}</span>
  </div>
  <div v-else class="flex flex-col gap-3 mb-3">
    <template v-for="field in fields" :key="field.fieldname">
      <Grid
        v-if="field.fieldtype === 'Table'"
        v-model="data.doc[field.fieldname]"
        :label="field.label"
        :fields="field.fields"
        :gridFields="field.gridFields"
      />
      <FormControl
        v-else
        type="text"
        v-model="data.doc[field.fieldname]"
        :label="field.label"
      />
    </template>
  </div>
</template>

<script setup>
import Grid from '@/components/Controls/Grid.vue'
import { Badge, createDocumentResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { createToast } from '@/utils'
import { ref, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
  meta: {
    type: Object,
    required: true,
  },
})

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.docname,
  cache: ['doc', props.docname],
  setValue: {
    onSuccess: () => {
      data.reload()
      createToast({
        title: 'Data Updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: 'Error',
        text: err.messages[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  },
})

const fields = computed(() => {
  if (!data.doc) return []
  if (!props.meta) return []
  return [
    // getFieldObj(props.meta.custom_product),
    {
      label: props.meta.status_change_log.df.label,
      fieldname: props.meta.status_change_log.df.fieldname,
      fieldtype: props.meta.status_change_log.df.fieldtype,
      ...getFields(
        props.meta.status_change_log.df.fieldname,
        props.meta.status_change_log.fields,
      ),
    },
    // {
    //   label: props.meta.contacts.df.label,
    //   fieldname: props.meta.contacts.df.fieldname,
    //   fieldtype: props.meta.contacts.df.fieldtype,
    //   ...getFields(
    //     props.meta.contacts.df.fieldname,
    //     props.meta.contacts.fields,
    //   ),
    // },
  ]
})

function getFields(name, fields) {
  fields = fields.map((field) => {
    return {
      ...getFieldObj(field),
      onChange: (value, index) => {
        data.doc[name][index][field.fieldname] = value
      },
    }
  })

  return {
    fields: fields,
    gridFields: fields.filter((field) => field.in_list_view),
  }
}

function getFieldObj(field) {
  return {
    label: field.label,
    fieldname: field.fieldname,
    fieldtype: field.fieldtype,
    options: field.options,
    in_list_view: field.in_list_view,
  }
}

function saveChanges() {
  data.save.submit()
}
</script>
