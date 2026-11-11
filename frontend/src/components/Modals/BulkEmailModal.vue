<template>
  <Dialog
    v-model:open="show"
    :title="__('Bulk Email')"
    size="xl"
  >
    <template #default>
      <div class="space-y-3.5 text-xs">
        <!-- Recipient Count Banner -->
        <div class="flex items-center justify-between rounded bg-surface-gray-2 p-3 dark:bg-surface-gray-8">
          <div class="flex items-center gap-2">
            <span class="lucide-mail size-4 text-ink-primary" />
            <span class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
              {{ __('Sending email to {0} selected recipient(s)', [recipientCount]) }}
            </span>
          </div>
          <!-- Mode Tabs -->
          <div class="flex items-center rounded border border-outline-gray-2 bg-surface-white p-0.5 dark:border-outline-gray-7 dark:bg-surface-gray-9">
            <button
              type="button"
              class="flex items-center gap-1.5 rounded px-3 py-1 font-medium transition-colors"
              :class="activeMode === 'preview' ? 'bg-surface-gray-9 text-surface-white dark:bg-surface-gray-2 dark:text-ink-gray-9' : 'text-ink-gray-6 hover:text-ink-gray-9 dark:text-ink-gray-4'"
              @click="switchToPreview"
            >
              <span class="lucide-eye size-3.5" />
              <span>{{ __('Preview') }}</span>
            </button>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded px-3 py-1 font-medium transition-colors"
              :class="activeMode === 'edit' ? 'bg-surface-gray-9 text-surface-white dark:bg-surface-gray-2 dark:text-ink-gray-9' : 'text-ink-gray-6 hover:text-ink-gray-9 dark:text-ink-gray-4'"
              @click="activeMode = 'edit'"
            >
              <span class="lucide-pen size-3.5" />
              <span>{{ __('Edit') }}</span>
            </button>
          </div>
        </div>

        <!-- Template Selector -->
        <div>
          <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
            {{ __('Email Template (Optional)') }}
          </label>
          <select
            v-model="selectedTemplate"
            class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            @change="applyTemplate"
          >
            <option value="">{{ __('Custom Message (No Template)') }}</option>
            <option
              v-for="tpl in emailTemplates"
              :key="tpl.name"
              :value="tpl.name"
            >
              {{ tpl.name }} ({{ tpl.subject || __('No Subject') }})
            </option>
          </select>
        </div>

        <!-- PREVIEW MODE -->
        <div v-if="activeMode === 'preview'" class="space-y-3">
          <!-- Preview Notice & Sample Info -->
          <div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-base px-3 py-2 dark:border-outline-gray-7">
            <div class="flex items-center gap-2 text-ink-gray-6 dark:text-ink-gray-3">
              <span class="lucide-sparkles size-3.5 text-ink-primary" />
              <span>
                {{ __('Previewing as received by sample recipient: {0} ({1})', [sampleRecipient.full_name, sampleRecipient.email]) }}
              </span>
            </div>
            <Button
              variant="subtle"
              size="sm"
              iconLeft="lucide-pen"
              :label="__('Edit Email')"
              @click="activeMode = 'edit'"
            />
          </div>

          <!-- Mock Email Envelope Preview -->
          <div class="rounded border border-outline-gray-2 bg-surface-white dark:border-outline-gray-7 dark:bg-surface-gray-9">
            <!-- Email Header Meta -->
            <div class="border-b border-outline-gray-2 p-3 space-y-1.5 bg-surface-gray-1 dark:border-outline-gray-7 dark:bg-surface-gray-8">
              <div class="flex items-center gap-2">
                <span class="w-16 font-semibold text-ink-gray-5">{{ __('Subject:') }}</span>
                <span class="font-medium text-ink-gray-9 dark:text-ink-white">{{ previewSubject || __('(No Subject)') }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-16 font-semibold text-ink-gray-5">{{ __('To:') }}</span>
                <span class="text-ink-gray-7 dark:text-ink-gray-3">{{ sampleRecipient.full_name }} &lt;{{ sampleRecipient.email }}&gt;</span>
              </div>
              <div v-if="sampleRecipient.organization" class="flex items-center gap-2">
                <span class="w-16 font-semibold text-ink-gray-5">{{ __('Company:') }}</span>
                <span class="text-ink-gray-7 dark:text-ink-gray-3">{{ sampleRecipient.organization }}</span>
              </div>
            </div>

            <!-- Email Body Rendered HTML -->
            <div
              v-if="previewContent"
              class="prose prose-sm max-h-[300px] overflow-y-auto p-4 text-xs text-ink-gray-9 dark:prose-invert dark:text-ink-white"
              v-html="previewContent"
            />
            <div
              v-else
              class="p-8 text-center text-xs text-ink-gray-4 italic"
            >
              {{ __('Email message body is empty. Click "Edit Email" to compose your message.') }}
            </div>
          </div>
        </div>

        <!-- EDIT MODE -->
        <div v-else class="space-y-3">
          <!-- Subject Input -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Subject *') }}
            </label>
            <input
              v-model="subject"
              type="text"
              :placeholder="__('Enter email subject...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <!-- Variable Pills helper -->
          <div>
            <div class="mb-1 flex items-center justify-between">
              <label class="font-medium text-ink-gray-7 dark:text-ink-gray-3">
                {{ __('Message Body *') }}
              </label>
              <div class="flex items-center gap-1.5">
                <span class="text-[11px] text-ink-gray-5">{{ __('Insert Variable:') }}</span>
                <button
                  v-for="v in personalizationVariables"
                  :key="v"
                  type="button"
                  class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-[10px] font-mono font-medium text-ink-gray-8 hover:bg-surface-gray-3 dark:bg-surface-gray-8 dark:text-ink-gray-2"
                  @click="insertVariable(v)"
                >
                  {{ v }}
                </button>
              </div>
            </div>

            <!-- Rich TipTap Editor -->
            <div class="rounded border border-outline-gray-2 bg-surface-white dark:border-outline-gray-7 dark:bg-surface-gray-9">
              <Editor
                v-model="content"
                :extensions="editorExtensions"
                :placeholder="__('Write your email message here...')"
              >
                <EditorFixedMenu
                  :items="editorToolbar"
                  class="w-full overflow-x-auto rounded-t border-b border-outline-gray-2 bg-surface-base p-1 dark:border-outline-gray-7"
                />
                <EditorContent class="prose prose-sm min-h-[160px] max-h-[300px] overflow-y-auto min-w-full p-3 text-xs text-ink-gray-9 dark:prose-invert dark:text-ink-white focus:outline-none" />
              </Editor>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMsg" class="text-xs font-medium text-ink-red-3">
          {{ errorMsg }}
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-2">
          <Button
            v-if="activeMode === 'edit'"
            variant="outline"
            size="sm"
            iconLeft="lucide-eye"
            :label="__('Preview with Sample Data')"
            @click="switchToPreview"
          />
          <Button
            v-else
            variant="outline"
            size="sm"
            iconLeft="lucide-pen"
            :label="__('Edit Content')"
            @click="activeMode = 'edit'"
          />
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            :disabled="sending"
            @click="show = false"
          />
          <Button
            variant="solid"
            iconLeft="lucide-send"
            :label="__('Send to {0} Recipients', [recipientCount])"
            :loading="sending"
            @click="submitBulkEmail"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Dialog, Button, call, toast } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu } from 'frappe-ui/editor'
import { buildEditorExtensions, formToolbar } from '@/components/editor/config'

const props = defineProps({
  doctype: { type: String, default: 'Contact' },
  selectedValues: { type: [Array, Set], default: () => [] },
})

const emit = defineEmits(['reload'])
const show = defineModel({ type: Boolean, default: false })

const subject = ref('')
const content = ref('')
const previewSubject = ref('')
const previewContent = ref('')
const activeMode = ref('preview')
const selectedTemplate = ref('')
const emailTemplates = ref([])
const sending = ref(false)
const errorMsg = ref('')

const sampleRecipient = ref({
  full_name: 'Alex Morgan',
  first_name: 'Alex',
  organization: 'Acme Corp',
  email: 'alex.morgan@example.com',
})

const personalizationVariables = [
  '{{ first_name }}',
  '{{ full_name }}',
  '{{ organization }}',
  '{{ email }}',
]

const editorExtensions = buildEditorExtensions()
const editorToolbar = formToolbar

const recipientCount = computed(() => {
  if (Array.isArray(props.selectedValues)) {
    return props.selectedValues.length
  }
  if (props.selectedValues && typeof props.selectedValues.size === 'number') {
    return props.selectedValues.size
  }
  return 0
})

function getFirstSelectedName() {
  if (Array.isArray(props.selectedValues) && props.selectedValues.length) {
    return props.selectedValues[0]
  }
  if (props.selectedValues && typeof props.selectedValues[Symbol.iterator] === 'function') {
    for (const val of props.selectedValues) {
      return val
    }
  }
  return null
}

onMounted(async () => {
  try {
    const list = await call('frappe.client.get_list', {
      doctype: 'Email Template',
      fields: ['name', 'subject', 'response', 'response_html', 'use_html'],
      filters: { enabled: 1 },
      order_by: 'modified desc',
      limit_page_length: 50,
    })
    emailTemplates.value = list || []
  } catch (err) {
    console.error('Failed to load email templates:', err)
  }

  // If there's a selected recipient, resolve sample data
  const sampleName = getFirstSelectedName()
  if (sampleName && props.doctype === 'Contact') {
    try {
      const contactDoc = await call('frappe.client.get', {
        doctype: 'Contact',
        name: sampleName,
      })
      if (contactDoc) {
        sampleRecipient.value = {
          full_name: contactDoc.full_name || `${contactDoc.first_name || ''} ${contactDoc.last_name || ''}`.strip() || sampleName,
          first_name: contactDoc.first_name || contactDoc.full_name?.split(' ')[0] || 'there',
          organization: contactDoc.company_name || 'Organization',
          email: contactDoc.email_id || contactDoc.email_ids?.[0]?.email_id || 'recipient@example.com',
        }
      }
    } catch (e) {
      // Keep default sample recipient
    }
  }
})

async function applyTemplate() {
  if (!selectedTemplate.value) {
    return
  }
  try {
    const sampleContact = props.doctype === 'Contact' ? getFirstSelectedName() : null
    const res = await call('crm.api.daily_allocation.render_email_template', {
      template_name: selectedTemplate.value,
      contact: sampleContact,
    })

    if (res) {
      subject.value = res.raw_subject || res.subject || ''
      content.value = res.raw_content || res.content || ''
      previewSubject.value = res.subject || ''
      previewContent.value = res.content || ''
      if (res.sample_recipient) {
        sampleRecipient.value = res.sample_recipient
      }
      activeMode.value = 'preview'
    }
  } catch (err) {
    console.error('Failed to render email template:', err)
  }
}

async function switchToPreview() {
  if (!content.value && !subject.value) {
    activeMode.value = 'preview'
    return
  }
  try {
    const sampleContact = props.doctype === 'Contact' ? getFirstSelectedName() : null
    const res = await call('crm.api.daily_allocation.render_email_preview', {
      content: content.value,
      subject: subject.value,
      contact: sampleContact,
    })
    if (res) {
      previewSubject.value = res.subject || subject.value
      previewContent.value = res.content || content.value
      if (res.sample_recipient) {
        sampleRecipient.value = res.sample_recipient
      }
    }
  } catch (e) {
    previewSubject.value = subject.value
    previewContent.value = content.value
  }
  activeMode.value = 'preview'
}

function insertVariable(v) {
  content.value = (content.value || '') + ` ${v} `
}

async function submitBulkEmail() {
  errorMsg.value = ''
  if (!subject.value.trim()) {
    errorMsg.value = __('Please enter an email subject.')
    return
  }
  if (!content.value.trim() || content.value.trim() === '<p></p>') {
    errorMsg.value = __('Please enter an email message.')
    return
  }

  const items = Array.isArray(props.selectedValues)
    ? props.selectedValues
    : Array.from(props.selectedValues || [])

  if (!items.length) {
    errorMsg.value = __('No recipients selected.')
    return
  }

  sending.value = true
  try {
    const res = await call('crm.api.daily_allocation.send_bulk_email', {
      doctype: props.doctype,
      names: items,
      subject: subject.value.trim(),
      content: content.value.trim(),
      template_name: selectedTemplate.value || null,
    })

    if (res.sent > 0) {
      toast.success(__('Successfully sent email to {0} recipient(s).', [res.sent]))
    }
    if (res.skipped > 0) {
      toast.warning(__('Skipped {0} recipient(s) without email.', [res.skipped]))
    }
    show.value = false
    emit('reload')
  } catch (err) {
    console.error('Bulk email error:', err)
    errorMsg.value = err.message || __('Failed to send bulk email.')
  } finally {
    sending.value = false
  }
}
</script>
