<template>
  <Dialog
    v-model:open="show"
    :title="__('Bulk Email')"
    size="xl"
  >
    <template #default>
      <div class="space-y-4 text-xs">
        <!-- Recipient Count Banner -->
        <div class="flex items-center gap-2 rounded bg-surface-gray-2 p-3 dark:bg-surface-gray-8">
          <span class="lucide-mail size-4 text-ink-primary" />
          <span class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
            {{ __('Sending email to {0} selected recipient(s)', [recipientCount]) }}
          </span>
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

        <!-- Content Area -->
        <div>
          <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
            {{ __('Message Body *') }}
          </label>
          <textarea
            v-model="content"
            rows="6"
            :placeholder="__('Write your message here...')"
            class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
          />
        </div>

        <!-- Error Message -->
        <div v-if="errorMsg" class="text-xs font-medium text-ink-red-3">
          {{ errorMsg }}
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
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
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Dialog, Button, call, toast } from 'frappe-ui'

const props = defineProps({
  doctype: { type: String, default: 'Contact' },
  selectedValues: { type: [Array, Set], default: () => [] },
})

const emit = defineEmits(['reload'])
const show = defineModel({ type: Boolean, default: false })

const subject = ref('')
const content = ref('')
const selectedTemplate = ref('')
const emailTemplates = ref([])
const sending = ref(false)
const errorMsg = ref('')

const recipientCount = computed(() => {
  if (Array.isArray(props.selectedValues)) {
    return props.selectedValues.length
  }
  if (props.selectedValues && typeof props.selectedValues.size === 'number') {
    return props.selectedValues.size
  }
  return 0
})

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
})

function applyTemplate() {
  if (!selectedTemplate.value) return
  const tpl = emailTemplates.value.find((t) => t.name === selectedTemplate.value)
  if (tpl) {
    if (tpl.subject) subject.value = tpl.subject
    content.value = tpl.response || tpl.response_html || ''
  }
}

async function submitBulkEmail() {
  errorMsg.value = ''
  if (!subject.value.trim()) {
    errorMsg.value = __('Please enter an email subject.')
    return
  }
  if (!content.value.trim()) {
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

