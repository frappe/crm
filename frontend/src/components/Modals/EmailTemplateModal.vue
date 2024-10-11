<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode ? __(emailTemplate.name) : __('Create Email Template'),
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => (editMode ? updateEmailTemplate() : callInsertDoc()),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex sm:flex-row flex-col gap-4">
          <div class="flex-1">
            <div class="mb-1.5 text-sm text-gray-600">
              {{ __('Name') }}
              <span class="text-red-500">*</span>
            </div>
            <TextInput
              ref="nameRef"
              variant="outline"
              v-model="_emailTemplate.name"
              :placeholder="__('Payment Reminder')"
            />
          </div>
          <div class="flex-1">
            <div class="mb-1.5 text-sm text-gray-600">{{ __('Doctype') }}</div>
            <Select
              variant="outline"
              v-model="_emailTemplate.reference_doctype"
              :options="['CRM Deal', 'CRM Lead']"
              :placeholder="__('CRM Deal')"
            />
          </div>
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">
            {{ __('Subject') }}
            <span class="text-red-500">*</span>
          </div>
          <TextInput
            ref="subjectRef"
            variant="outline"
            v-model="_emailTemplate.subject"
            :placeholder="__('Payment Reminder from Frappé - (#{{ name }})')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">
            {{ __('Content Type') }}
          </div>
          <Select
            variant="outline"
            v-model="_emailTemplate.content_type"
            default="Rich Text"
            :options="['Rich Text', 'HTML']"
            :placeholder="__('Rich Text')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">
            {{ __('Content') }}
            <span class="text-red-500">*</span>
          </div>
          <FormControl
            v-if="_emailTemplate.content_type === 'HTML'"
            type="textarea"
            variant="outline"
            ref="content"
            :rows="10"
            v-model="_emailTemplate.response_html"
            :placeholder="
              __(
                '<p>Dear {{ lead_name }},</p>\n\n<p>This is a reminder for the payment of {{ grand_total }}.</p>\n\n<p>Thanks,</p>\n<p>Frappé</p>',
              )
            "
          />
          <TextEditor
            v-else
            variant="outline"
            ref="content"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubbleMenu="true"
            :content="_emailTemplate.response"
            @change="(val) => (_emailTemplate.response = val)"
            :placeholder="
              __(
                'Dear {{ lead_name }}, \n\nThis is a reminder for the payment of {{ grand_total }}. \n\nThanks, \nFrappé',
              )
            "
          />
        </div>
        <div>
          <Checkbox v-model="_emailTemplate.enabled" :label="__('Enabled')" />
        </div>
        <ErrorMessage :message="__(errorMessage)" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { capture } from '@/telemetry'
import { Checkbox, Select, TextEditor, call } from 'frappe-ui'
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  emailTemplate: {
    type: Object,
    default: {},
  },
})

const show = defineModel()
const emailTemplates = defineModel('reloadEmailTemplates')
const errorMessage = ref('')

const emit = defineEmits(['after'])

const subjectRef = ref(null)
const nameRef = ref(null)
const editMode = ref(false)
let _emailTemplate = ref({
  content_type: 'Rich Text',
})

async function updateEmailTemplate() {
  if (!validate()) return
  const old = { ...props.emailTemplate }
  const newEmailTemplate = { ..._emailTemplate.value }

  const nameChanged = old.name !== newEmailTemplate.name
  delete old.name
  delete newEmailTemplate.name

  const otherFieldChanged =
    JSON.stringify(old) !== JSON.stringify(newEmailTemplate)
  const values = newEmailTemplate

  if (!nameChanged && !otherFieldChanged) {
    show.value = false
    return
  }

  let name
  if (nameChanged) {
    name = await callRenameDoc()
  }
  if (otherFieldChanged) {
    name = await callSetValue(values)
  }
  handleEmailTemplateUpdate({ name })
}

async function callRenameDoc() {
  const d = await call('frappe.client.rename_doc', {
    doctype: 'Email Template',
    old_name: props.emailTemplate.name,
    new_name: _emailTemplate.value.name,
  })
  return d
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'Email Template',
    name: _emailTemplate.value.name,
    fieldname: values,
  })
  return d.name
}

async function callInsertDoc() {
  if (!validate()) return
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'Email Template',
      ..._emailTemplate.value,
    },
  })
  if (doc.name) {
    capture('email_template_created', { doctype: doc.reference_doctype })
    handleEmailTemplateUpdate(doc)
  }
}

function handleEmailTemplateUpdate(doc) {
  emailTemplates.value?.reload()
  show.value = false
}

function validate() {
  _emailTemplate.value.use_html = Boolean(
    _emailTemplate.value.content_type == 'HTML',
  )
  if (!_emailTemplate.value.name) {
    errorMessage.value = 'Name is required'
    return false
  }
  if (!_emailTemplate.value.subject) {
    errorMessage.value = 'Subject is required'
    return false
  }
  if (
    !_emailTemplate.value.use_html &&
    (!_emailTemplate.value.response ||
      _emailTemplate.value.response === '<p></p>')
  ) {
    errorMessage.value = 'Content is required'
    return false
  }
  if (_emailTemplate.value.use_html && !_emailTemplate.value.response_html) {
    errorMessage.value = 'Content is required'
    return false
  }
  return true
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    errorMessage.value = ''
    nextTick(() => {
      if (_emailTemplate.value.name) {
        subjectRef.value.el.focus()
      } else {
        nameRef.value.el.focus()
      }
      _emailTemplate.value = { ...props.emailTemplate }
      _emailTemplate.value.content_type = _emailTemplate.value.use_html
        ? 'HTML'
        : 'Rich Text'
      if (_emailTemplate.value.name) {
        editMode.value = true
      }
    })
  },
)
</script>
