<template>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <Textarea
      ref="textareaRef"
      v-model="content"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      :placeholder="__('Type your SMS here...')"
      @focus="rows = 4"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
    <Button
      variant="solid"
      :label="__('Send')"
      :disabled="!content.trim()"
      @click="sendSMS"
    />
  </div>
</template>

<script setup>
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource, Textarea, toast } from 'frappe-ui'
import { ref, nextTick } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const sms = defineModel('sms', { type: Object, default: () => ({}) })

const { capture } = useTelemetry()

const rows = ref(1)
const textareaRef = ref(null)
const content = ref('')

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  sendSMS()
  textareaRef.value.el?.blur()
}

function sendSMS() {
  if (!content.value.trim()) return
  const message = content.value
  content.value = ''
  capture('sms_send_message')
  createResource({
    url: 'crm.api.sms.send_sms',
    params: {
      reference_doctype: props.doctype,
      reference_name: doc.value.name,
      to: doc.value.mobile_no,
      message,
    },
    auto: true,
    onSuccess: () => sms.value.reload(),
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to send SMS'))
    },
  })
}

defineExpose({ show })
</script>
