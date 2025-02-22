<template>
  <Dialog
    v-model="dialogShow"
    :options="{
      title: editMode ? __(_emailTemplate.name) : __('Create Email Template'),
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
            <FormControl
              ref="nameRef"
              v-model="_emailTemplate.name"
              :placeholder="__('Payment Reminder')"
              :label="__('Name')"
              :required="true"
              @update:modelValue="handleFieldChange"
            />
          </div>
          <div class="flex-1">
            <FormControl
              type="select"
              v-model="_emailTemplate.reference_doctype"
              :label="__('Doctype')"
              :options="['CRM Deal', 'CRM Lead']"
              :placeholder="__('CRM Deal')"
              @update:modelValue="handleFieldChange"
            />
          </div>
        </div>
        <div>
          <FormControl
            ref="subjectRef"
            v-model="_emailTemplate.subject"
            :label="__('Subject')"
            :placeholder="__('Payment Reminder from Frappé - (#{{ name }})')"
            :required="true"
            @update:modelValue="handleFieldChange"
          />
        </div>
        <div>
          <FormControl
            type="select"
            v-model="_emailTemplate.content_type"
            :label="__('Content Type')"
            default="Rich Text"
            :options="['Rich Text', 'HTML']"
            :placeholder="__('Rich Text')"
            @update:modelValue="handleFieldChange"
          />
        </div>
        <div>
          <FormControl
            v-if="_emailTemplate.content_type === 'HTML'"
            type="textarea"
            :label="__('Content')"
            :required="true"
            ref="content"
            :rows="10"
            v-model="_emailTemplate.response_html"
            :placeholder="
              __(
                '<p>Dear {{ lead_name }},</p>\n\n<p>This is a reminder for the payment of {{ grand_total }}.</p>\n\n<p>Thanks,</p>\n<p>Frappé</p>',
              )
            "
            @update:modelValue="handleFieldChange"
          />
          <div v-else>
            <div class="mb-1.5 text-xs text-ink-gray-5">
              {{ __('Content') }}
              <span class="text-ink-red-3">*</span>
            </div>
            <TextEditor
              ref="content"
              editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
              :bubbleMenu="true"
              :content="_emailTemplate.response"
              @change="(val) => { _emailTemplate.response = val; handleFieldChange(); }"
              :placeholder="
                __(
                  'Dear {{ lead_name }}, \n\nThis is a reminder for the payment of {{ grand_total }}. \n\nThanks, \nFrappé',
                )
              "
            />
          </div>
        </div>
        <div>
          <Checkbox v-model="_emailTemplate.enabled" :label="__('Enabled')" />
        </div>
        <ErrorMessage :message="__(errorMessage)" />
      </div>
    </template>
  </Dialog>
  <ConfirmCloseDialog 
    v-model="showConfirmClose"
    @confirm="confirmClose"
    @cancel="cancelClose"
  />
</template>

<script setup>
import ConfirmCloseDialog from '@/components/Modals/ConfirmCloseDialog.vue'
import { capture } from '@/telemetry'
import { Checkbox, TextEditor, call } from 'frappe-ui'
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  emailTemplate: {
    type: Object,
    default: {},
  },
})

const show = defineModel()
const dialogShow = ref(false)
const showConfirmClose = ref(false)
const emailTemplates = defineModel('reloadEmailTemplates')
const errorMessage = ref('')

const nameRef = ref(null)
const subjectRef = ref(null)
const editMode = ref(false)
const isDirty = ref(false)
let _emailTemplate = ref({
  content_type: 'Rich Text',
})

watch(
  () => show.value,
  (value) => {
    if (value === dialogShow.value) return
    if (value) {
      _emailTemplate.value = { ...props.emailTemplate }
      editMode.value = !!props.emailTemplate.name
      isDirty.value = false
      dialogShow.value = true
    }
  },
  { immediate: true }
)

watch(
  () => dialogShow.value,
  (value) => {
    if (value) return
    if (isDirty.value) {
      showConfirmClose.value = true
      nextTick(() => {
        dialogShow.value = true
      })
    } else {
      show.value = false
    }
  }
)

function handleFieldChange() {
  isDirty.value = true
}

function handleClose() {
  if (isDirty.value) {
    showConfirmClose.value = true
  } else {
    dialogShow.value = false
    show.value = false
  }
}

function confirmClose() {
  isDirty.value = false
  dialogShow.value = false
  show.value = false
}

function cancelClose() {
  showConfirmClose.value = false
}

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
    handleClose()
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
  handleClose()
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
</script>
