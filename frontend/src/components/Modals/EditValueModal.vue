<template>
  <Dialog v-model:open="show" :title="__('Bulk Edit')">
    <div v-if="fields.length" class="mb-4">
      <Combobox
        :model-value="field.fieldname"
        :label="__('Field')"
        :options="fields"
        class="w-full"
        :placeholder="__('Source')"
        :openOnClick="true"
        @update:selectedOption="(e) => changeField(e)"
      />
    </div>
    <div>
      <div class="mb-1.5 text-p-sm font-medium text-ink-gray-7">
        {{ __('Value') }}
      </div>
      <component
        :is="getValueComponent(field)"
        :value="newValue"
        :placeholder="__('Contact Us')"
        @change="(v) => updateValue(v)"
      />
    </div>
    <ErrorMessage class="mt-2" :message="error" />
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :loading="loading"
          :label="__('Update {0} Records', [recordCount])"
          @click="updateValues"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { getMeta } from '@/stores/meta'
import { useTelemetry, Link } from 'frappe-ui/frappe'
import {
  Combobox,
  Select,
  call,
  TextEditor,
  DatePicker,
  ErrorMessage,
  TextInput,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link', 'User']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeEditor = ['Text Editor']
const typeDate = ['Date', 'Datetime']

const props = defineProps({
  doctype: { type: String, required: true },
  selectedValues: { type: Set, required: true },
})

const show = defineModel({ type: Boolean })

const emit = defineEmits(['reload'])

const { capture } = useTelemetry()

const { getFields } = getMeta(props.doctype)

const fields = computed(() => {
  const _fields =
    getFields({ restrictedFieldTypes: ['Read Only'] })?.filter(
      (f) => !f.read_only,
    ) || []
  return _fields.map((f) => ({ ...f, value: f.fieldname }))
})

const recordCount = computed(() => props.selectedValues?.size || 0)

const field = ref({
  label: '',
  fieldtype: '',
  fieldname: '',
  options: '',
})

const newValue = ref('')
const loading = ref(false)
const error = ref('')

function updateValues() {
  error.value = ''

  if (!field.value.fieldname) {
    error.value = __('Please select a field to update')
    return
  }

  let fieldVal = newValue.value
  if (field.value.fieldtype == 'Check') {
    fieldVal = fieldVal == 'Yes' ? 1 : 0
  }
  loading.value = true
  call(
    'frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs',
    {
      doctype: props.doctype,
      docnames: Array.from(props.selectedValues),
      action: 'update',
      data: {
        [field.value.fieldname]: fieldVal || null,
      },
    },
  ).then(() => {
    field.value = {
      label: '',
      fieldtype: '',
      fieldname: '',
      options: '',
    }
    newValue.value = ''
    loading.value = false
    error.value = ''
    show.value = false
    capture('bulk_update', { doctype: props.doctype })
    emit('reload')
  })
}

function changeField(f) {
  newValue.value = ''
  if (!f) return
  field.value = f
}

function updateValue(v) {
  let value = v.target ? v.target.value : v
  newValue.value = value
}

function getValueComponent(f) {
  const { fieldtype, options } = f
  if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == 'Check'
        ? [
            { label: 'Yes', value: 'Yes' },
            { label: 'No', value: 'No' },
          ]
        : options
    return h(Select, {
      class: 'w-full',
      options: _options,
      modelValue: newValue.value,
    })
  } else if (typeLink.includes(fieldtype)) {
    if (fieldtype == 'Dynamic Link') {
      return h(TextInput)
    }
    return h(Link, {
      class: 'form-control w-full',
      doctype: fieldtype == 'User' ? 'User' : options,
      modelValue: newValue.value,
      'onUpdate:modelValue': (v) => updateValue(v),
    })
  } else if (typeNumber.includes(fieldtype)) {
    return h(TextInput, { type: 'number' })
  } else if (typeDate.includes(fieldtype)) {
    return h(DatePicker)
  } else if (typeEditor.includes(fieldtype)) {
    return h(TextEditor, {
      variant: 'outline',
      editorClass:
        '!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors',
      bubbleMenu: true,
      content: newValue.value,
    })
  } else {
    return h(TextInput)
  }
}
</script>
