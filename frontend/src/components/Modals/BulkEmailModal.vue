<template>
  <Dialog
    v-model:open="show"
    :title="__('Bulk Email')"
    size="xl"
  >
    <template #default>
      <div class="space-y-3.5">
        <VisualEmailEditor
          ref="visualEditorRef"
          v-model:subject="subject"
          v-model:content="content"
          v-model:templateName="selectedTemplate"
          v-model:isBranded="isBranded"
          :recipientCount="recipientCount"
          :sampleRecipient="sampleRecipient"
          :contactName="sampleContactName"
          defaultMode="preview"
        />

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
            v-if="visualEditorRef?.activeMode === 'edit'"
            variant="outline"
            size="sm"
            iconLeft="lucide-eye"
            :label="__('Preview with Sample Data')"
            @click="visualEditorRef?.switchToPreview()"
          />
          <Button
            v-else
            variant="outline"
            size="sm"
            iconLeft="lucide-pen"
            :label="__('Edit Content')"
            @click="if (visualEditorRef) visualEditorRef.activeMode = 'edit'"
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
import VisualEmailEditor from '@/components/VisualEmailEditor.vue'

const props = defineProps({
  doctype: { type: String, default: 'Contact' },
  selectedValues: { type: [Array, Set], default: () => [] },
})

const emit = defineEmits(['reload'])
const show = defineModel({ type: Boolean, default: false })

const visualEditorRef = ref(null)
const subject = ref('')
const content = ref('')
const selectedTemplate = ref('Demo')
const isBranded = ref(true)
const sending = ref(false)
const errorMsg = ref('')

const sampleRecipient = ref({
  full_name: 'Alex Morgan',
  first_name: 'Alex',
  organization: 'Acme Corp',
  email: 'alex.morgan@example.com',
})

const recipientCount = computed(() => {
  if (Array.isArray(props.selectedValues)) {
    return props.selectedValues.length
  }
  if (props.selectedValues && typeof props.selectedValues.size === 'number') {
    return props.selectedValues.size
  }
  return 0
})

const sampleContactName = computed(() => {
  if (Array.isArray(props.selectedValues) && props.selectedValues.length) {
    return props.selectedValues[0]
  }
  if (props.selectedValues && typeof props.selectedValues[Symbol.iterator] === 'function') {
    for (const val of props.selectedValues) {
      return val
    }
  }
  return null
})

onMounted(async () => {
  // If there's a selected recipient, resolve sample data
  const sampleName = sampleContactName.value
  if (sampleName && props.doctype === 'Contact') {
    try {
      const contactDoc = await call('frappe.client.get', {
        doctype: 'Contact',
        name: sampleName,
      })
      if (contactDoc) {
        sampleRecipient.value = {
          full_name:
            contactDoc.full_name ||
            `${contactDoc.first_name || ''} ${contactDoc.last_name || ''}`.trim() ||
            sampleName,
          first_name:
            contactDoc.first_name ||
            contactDoc.full_name?.split(' ')[0] ||
            'there',
          organization: contactDoc.company_name || 'Organization',
          email:
            contactDoc.email_id ||
            contactDoc.email_ids?.[0]?.email_id ||
            'recipient@example.com',
        }
      }
    } catch (e) {
      // Keep default sample recipient
    }
  }
})

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
      is_branded: isBranded.value,
    })

    if (res.sent > 0) {
      toast.success(
        __('Successfully sent email to {0} recipient(s).', [res.sent]),
      )
    }
    if (res.skipped > 0) {
      toast.warning(
        __('Skipped {0} recipient(s) without email.', [res.skipped]),
      )
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
