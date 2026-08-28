<template>
  <Dialog v-model:open="show" :title="__('Bulk Edit')">
    <template #default>
      <div class="mb-4">
        <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Field') }}</div>
        <Combobox
          class="w-full"
          trigger="button"
          :model-value="field.fieldname"
          :options="fields.data || []"
          :placeholder="__('Source')"
          @update:selected-option="(e) => changeField(e)"
        />
      </div>
      <div>
        <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Value') }}</div>
        <component
          :is="getValueComponent(field)"
          :value="newValue"
          size="md"
          :placeholder="__('Contact Us')"
          @change="(v) => updateValue(v)"
        />
      </div>
      <template v-if="isLostStatus">
        <div class="mt-4">
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Lost Reason') }}
            <span class="text-ink-red-5">*</span>
          </div>
          <Link
            ref="lostReasonLinkRef"
            class="form-control flex-1 truncate"
            :value="lostReason"
            doctype="CRM Lost Reason"
            :onCreate="onCreateLostReason"
            @change="(v) => (lostReason = v)"
          />
        </div>
        <div class="mt-4">
          <div class="mb-1.5 text-sm text-ink-gray-5">
            {{ __('Lost Notes') }}
            <span v-if="lostReason == 'Other'" class="text-ink-red-5">*</span>
          </div>
          <FormControl
            class="form-control flex-1 truncate"
            type="textarea"
            :value="lostNotes"
            @change="(e) => (lostNotes = e.target.value)"
          />
        </div>
      </template>
      <ErrorMessage v-if="error" class="mt-4" :message="error" />
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :loading="loading"
        :label="__('Update {0} Records', [recordCount])"
        @click="updateValues"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
<<<<<<< HEAD
import TextEditorControl from '@/components/Controls/TextEditorControl.vue'
=======
import { statusesStore } from '@/stores/statuses'
import { createDocument } from '@/composables/document'
>>>>>>> 6bfbd08 (fix: bulk edit silently reports success when records fail to save)
import { useTelemetry } from 'frappe-ui/frappe'
import {
  Combobox,
  FormControl,
  ErrorMessage,
  call,
  createResource,
<<<<<<< HEAD
=======
  toast,
  TextEditor,
>>>>>>> 6bfbd08 (fix: bulk edit silently reports success when records fail to save)
  DatePicker,
} from 'frappe-ui'
import { ref, computed, onMounted, h } from 'vue'

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link']
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

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
  },
  transform: (data) => {
    // `description` renders as a second line in the dropdown, which has no
    // max width, so a long one stretches the whole list.
    return (
      data
        .filter((f) => f.hidden == 0 && f.read_only == 0)
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        .map(({ description, ...f }) => ({ ...f, value: f.fieldname }))
    )
  },
})

onMounted(() => {
  if (fields.data?.length) return
  fields.fetch()
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

const { getLeadStatus, getDealStatus } = statusesStore()

const lostReason = ref('')
const lostNotes = ref('')
const lostReasonLinkRef = ref(null)

const isLostStatus = computed(() => {
  if (field.value.fieldname !== 'status' || !newValue.value) return false
  if (props.doctype === 'CRM Lead') {
    return getLeadStatus(newValue.value)?.type === 'Lost'
  }
  if (props.doctype === 'CRM Deal') {
    return getDealStatus(newValue.value)?.type === 'Lost'
  }
  return false
})

console.log('asim isLostStatus', isLostStatus.value)

function onCreateLostReason(value, close) {
  console.log('asim onCreateLostReason', value, close)
  createDocument('CRM Lost Reason', { lost_reason: value }, close, (doc) => {
    lostReason.value = doc.name
    lostReasonLinkRef.value?.reload('', true)
  })
}

function updateValues() {
  error.value = ''
  let fieldVal = newValue.value
  if (field.value.fieldtype == 'Check') {
    fieldVal = fieldVal == 'Yes' ? 1 : 0
  }

  let data = { [field.value.fieldname]: fieldVal || null }
  if (isLostStatus.value) {
    if (!lostReason.value) {
      error.value = __('Lost Reason is required')
      return
    }
    if (lostReason.value === 'Other' && !lostNotes.value) {
      error.value = __('Lost Notes are required when Lost Reason is "Other"')
      return
    }
    data.lost_reason = lostReason.value
    data.lost_notes = lostNotes.value
  }

  loading.value = true
  call(
    'frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs',
    {
      doctype: props.doctype,
      docnames: Array.from(props.selectedValues),
      action: 'update',
      data,
    },
  ).then((failed) => {
    loading.value = false
    // Response is the list of docnames that failed to save, or null when the
    // operation was enqueued (>= 20 records).
    if (Array.isArray(failed) && failed.length) {
      error.value = __('Failed to update {0} record(s): {1}', [
        failed.length,
        failed.join(', '),
      ])
      emit('reload')
      return
    }
    field.value = {
      label: '',
      fieldtype: '',
      fieldname: '',
      options: '',
    }
    newValue.value = ''
    lostReason.value = ''
    lostNotes.value = ''
    show.value = false
    capture('bulk_update', { doctype: props.doctype })
    emit('reload')
    if (!Array.isArray(failed)) {
      toast.info(
        __(
          'Bulk operation is enqueued in background. Failures, if any, are recorded in Error Log.',
        ),
      )
    }
  })
}

function changeField(f) {
  newValue.value = ''
  lostReason.value = ''
  lostNotes.value = ''
  error.value = ''
  if (!f) return
  field.value = f
}

function updateValue(v) {
  let value = v.target ? v.target.value : v
  newValue.value = value
}

function getSelectOptions(options) {
  return options.split('\n')
}

function getValueComponent(f) {
  const { fieldtype, options } = f
  if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == 'Check' ? ['Yes', 'No'] : getSelectOptions(options)
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
      modelValue: newValue.value,
    })
  } else if (typeLink.includes(fieldtype)) {
    if (fieldtype == 'Dynamic Link') {
      return h(FormControl, { type: 'text' })
    }
    return h(Link, { class: 'form-control', doctype: options })
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: 'number' })
  } else if (typeDate.includes(fieldtype)) {
    return h(DatePicker)
  } else if (typeEditor.includes(fieldtype)) {
    return h(TextEditorControl, {
      variant: 'outline',
      editorClass:
        '!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-outline-gray-2 bg-surface-base hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-base focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors',
      fixedMenu: false,
      bubbleMenu: true,
      value: newValue.value,
    })
  } else {
    return h(FormControl, { type: 'text' })
  }
}
</script>
