<template>
  <div class="space-y-3.5 text-xs">
    <!-- Header Banner: Recipient Info & Mode Switcher -->
    <div class="flex items-center justify-between rounded bg-surface-gray-2 p-2.5 dark:bg-surface-gray-8">
      <div class="flex items-center gap-2">
        <span class="lucide-mail size-4 text-ink-primary" />
        <span class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
          <template v-if="recipientCount > 1">
            {{ __('Sending to {0} selected recipients', [recipientCount]) }}
          </template>
          <template v-else-if="sampleRecipient?.email">
            {{ __('Sending to: {0}', [sampleRecipient.full_name ? `${sampleRecipient.full_name} <${sampleRecipient.email}>` : sampleRecipient.email]) }}
          </template>
          <template v-else>
            {{ __('Email Composer') }}
          </template>
        </span>
      </div>

      <!-- Mode Toggle Buttons -->
      <div class="flex items-center rounded border border-outline-gray-2 bg-surface-white p-0.5 dark:border-outline-gray-7 dark:bg-surface-gray-9">
        <button
          type="button"
          class="flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors"
          :class="activeMode === 'preview' ? 'bg-surface-gray-9 text-surface-white dark:bg-surface-gray-2 dark:text-ink-gray-9' : 'text-ink-gray-6 hover:text-ink-gray-9 dark:text-ink-gray-4'"
          @click="switchToPreview"
        >
          <span class="lucide-eye size-3.5" />
          <span>{{ __('Preview') }}</span>
        </button>
        <button
          type="button"
          class="flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors"
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
        {{ __('Email Template') }}
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

    <!-- ============================================== -->
    <!-- PREVIEW MODE (Gmail-Style Realistic Rendering) -->
    <!-- ============================================== -->
    <div v-if="activeMode === 'preview'" class="space-y-2.5">
      <!-- Representative Prospect Banner -->
      <div class="flex items-center justify-between rounded border border-outline-gray-2 bg-surface-base px-3 py-2 dark:border-outline-gray-7">
        <div class="flex items-center gap-2 text-ink-gray-7 dark:text-ink-gray-3">
          <span class="lucide-sparkles size-4 text-ink-primary shrink-0" />
          <span class="text-[11px] leading-relaxed">
            <template v-if="recipientCount > 1">
              {{ __('Previewing as representative prospect: {0} ({1}). Recipient-specific variables (e.g. {{ first_name }}) will be personalized individually for each recipient when sending.', [sampleRecipient.full_name, sampleRecipient.email]) }}
            </template>
            <template v-else>
              {{ __('Previewing email as received by {0} ({1})', [sampleRecipient.full_name, sampleRecipient.email]) }}
            </template>
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

      <!-- Mock Email Envelope Container -->
      <div class="rounded border border-outline-gray-2 bg-surface-white overflow-hidden shadow-xs dark:border-outline-gray-7 dark:bg-surface-gray-9">
        <!-- Envelope Meta Header -->
        <div class="border-b border-outline-gray-2 bg-surface-gray-1 p-3 space-y-1.5 dark:border-outline-gray-7 dark:bg-surface-gray-8">
          <div class="flex items-center gap-2">
            <span class="w-16 font-semibold text-ink-gray-5">{{ __('Subject:') }}</span>
            <span class="font-medium text-ink-gray-9 dark:text-ink-white">{{ previewSubject || subject || __('(No Subject)') }}</span>
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

        <!-- Rendered Email Iframe -->
        <div class="bg-surface-white min-h-[280px] max-h-[380px] overflow-y-auto">
          <iframe
            v-if="previewContent"
            ref="previewIframe"
            :srcdoc="previewContent"
            class="w-full min-h-[340px] border-none bg-surface-white"
            sandbox="allow-same-origin"
          />
          <div
            v-else
            class="p-8 text-center text-xs text-ink-gray-4 italic"
          >
            {{ __('Email message body is empty. Click "Edit" to compose your message.') }}
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================== -->
    <!-- EDIT MODE (Visual WYSIWYG & Branded Shell)    -->
    <!-- ============================================== -->
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

      <!-- Variable Insertion Bar -->
      <div class="flex items-center justify-between">
        <label class="font-medium text-ink-gray-7 dark:text-ink-gray-3">
          {{ __('Message Body *') }}
        </label>
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] text-ink-gray-5">{{ __('Insert Variable:') }}</span>
          <button
            v-for="v in personalizationVariables"
            :key="v"
            type="button"
            class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-[10px] font-mono font-medium text-ink-gray-8 hover:bg-surface-gray-3 dark:bg-surface-gray-8 dark:text-ink-gray-2 transition-colors"
            @click="insertVariable(v)"
          >
            {{ v }}
          </button>
        </div>
      </div>

      <!-- VISUAL EDITOR CONTAINER -->
      <div class="rounded border border-outline-gray-2 bg-surface-white overflow-hidden dark:border-outline-gray-7 dark:bg-surface-gray-9">
        <!-- Visual Header if Branded Template Active -->
        <div
          v-if="isBranded"
          class="bg-[#080808] p-4 text-surface-white border-b border-[#222]"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="text-base font-extrabold tracking-wide text-white">
                SMRIKAAM TECHNOLOGIES
              </div>
              <div class="text-[9px] font-bold tracking-widest text-neutral-400">
                PROGRESS THROUGH INNOVATION
              </div>
            </div>
            <div class="text-right text-[9px] font-bold tracking-widest text-neutral-400">
              AI &amp; ML | Advance Analytics | Agentic AI | Cloud &amp; Big Data | IIoT
            </div>
          </div>
        </div>

        <!-- Rich TipTap Editor -->
        <Editor
          ref="editorRef"
          v-model="content"
          :extensions="editorExtensions"
          :placeholder="__('Write your email message here...')"
        >
          <EditorFixedMenu
            :items="editorToolbar"
            class="w-full overflow-x-auto border-b border-outline-gray-2 bg-surface-base p-1 dark:border-outline-gray-7"
          />
          <EditorContent class="prose prose-sm min-h-[160px] max-h-[300px] overflow-y-auto min-w-full p-4 text-xs text-ink-gray-9 dark:prose-invert dark:text-ink-white focus:outline-none" />
        </Editor>

        <!-- Visual Signature & Footer if Branded Template Active -->
        <div
          v-if="isBranded"
          class="border-t border-outline-gray-2 bg-surface-gray-1 p-4 space-y-3 dark:border-outline-gray-7 dark:bg-surface-gray-8"
        >
          <div class="flex items-center justify-between">
            <div class="text-xs text-ink-gray-7 space-y-0.5 dark:text-ink-gray-3">
              <div class="text-ink-gray-5">{{ __('Best regards,') }}</div>
              <div class="font-semibold text-ink-gray-9 dark:text-ink-white">{{ senderName }}</div>
              <div class="text-[11px] text-ink-gray-5">Smrikaam Technologies</div>
            </div>
            <div>
              <span class="inline-block rounded bg-[#111] px-4 py-1.5 text-[11px] font-bold text-white tracking-wider">
                AI&amp;ML &rarr;
              </span>
            </div>
          </div>
          <div class="border-t border-outline-gray-2 pt-2 flex items-center justify-between text-[9px] font-semibold tracking-wider text-ink-gray-5">
            <span>SMRIKAAM TECHNOLOGIES</span>
            <span>AI &bull; DATA &bull; CLOUD &bull; INDUSTRIAL IoT</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Button, call } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu } from 'frappe-ui/editor'
import { buildEditorExtensions, formToolbar } from '@/components/editor/config'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

const props = defineProps({
  subject: { type: String, default: '' },
  content: { type: String, default: '' },
  templateName: { type: String, default: '' },
  isBranded: { type: Boolean, default: false },
  recipientCount: { type: Number, default: 1 },
  sampleRecipient: {
    type: Object,
    default: () => ({
      full_name: 'Alex Morgan',
      first_name: 'Alex',
      organization: 'Acme Corp',
      email: 'alex.morgan@example.com',
    }),
  },
  contactName: { type: String, default: null },
  defaultMode: { type: String, default: 'preview' },
})

const emit = defineEmits([
  'update:subject',
  'update:content',
  'update:templateName',
  'update:isBranded',
])

const { user: sessionUser } = sessionStore()
const { getUser } = usersStore()

const senderName = computed(() => {
  const u = getUser(sessionUser)
  return u?.full_name || sessionUser || 'User'
})

const activeMode = ref(props.defaultMode)
const subject = ref(props.subject)
const content = ref(props.content)
const selectedTemplate = ref(props.templateName)
const isBranded = ref(props.isBranded)
const previewSubject = ref('')
const previewContent = ref('')
const emailTemplates = ref([])
const editorRef = ref(null)

const personalizationVariables = [
  '{{ first_name }}',
  '{{ full_name }}',
  '{{ organization }}',
  '{{ email }}',
]

const editorExtensions = buildEditorExtensions()
const editorToolbar = formToolbar

watch(subject, (val) => emit('update:subject', val))
watch(content, (val) => emit('update:content', val))
watch(selectedTemplate, (val) => emit('update:templateName', val))
watch(isBranded, (val) => emit('update:isBranded', val))

watch(
  () => props.subject,
  (val) => {
    if (val !== subject.value) subject.value = val
  },
)

watch(
  () => props.content,
  (val) => {
    if (val !== content.value) content.value = val
  },
)

onMounted(async () => {
  try {
    const list = await call('crm.api.daily_allocation.get_email_templates')
    emailTemplates.value = list || []
  } catch (err) {
    try {
      const list = await call('frappe.client.get_list', {
        doctype: 'Email Template',
        fields: ['name', 'subject', 'response', 'response_html', 'use_html'],
        filters: { enabled: 1 },
        order_by: 'modified desc',
        limit_page_length: 50,
      })
      emailTemplates.value = list || []
    } catch (e) {
      console.error('Failed to load email templates:', e)
    }
  }

  // If initial template provided or content present, render preview
  if (props.templateName) {
    selectedTemplate.value = props.templateName
    await applyTemplate()
  } else if (content.value || subject.value) {
    await switchToPreview()
  }
})

async function applyTemplate() {
  if (!selectedTemplate.value) {
    isBranded.value = false
    return
  }
  try {
    const res = await call('crm.api.daily_allocation.render_email_template', {
      template_name: selectedTemplate.value,
      contact: props.contactName || null,
    })

    if (res) {
      isBranded.value = !!res.is_branded
      subject.value = res.raw_subject || res.subject || ''
      content.value = res.body_content || res.raw_content || res.content || ''
      previewSubject.value = res.subject || ''
      previewContent.value = res.content || ''
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
    const res = await call('crm.api.daily_allocation.render_email_preview', {
      content: content.value,
      subject: subject.value,
      contact: props.contactName || null,
      template_name: selectedTemplate.value || null,
      is_branded: isBranded.value,
    })
    if (res) {
      previewSubject.value = res.subject || subject.value
      previewContent.value = res.content || content.value
    }
  } catch (err) {
    console.error('Failed to render email preview:', err)
  }
  activeMode.value = 'preview'
}

function insertVariable(variable) {
  if (editorRef.value?.editor) {
    editorRef.value.editor.commands.insertContent(variable)
    editorRef.value.editor.commands.focus()
  } else {
    content.value = (content.value ? content.value + ' ' : '') + variable
  }
}

defineExpose({
  subject,
  content,
  selectedTemplate,
  isBranded,
  previewSubject,
  previewContent,
  activeMode,
  switchToPreview,
  applyTemplate,
})
</script>
