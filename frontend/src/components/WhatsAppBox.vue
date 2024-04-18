<template>
  <div class="flex items-end gap-2 px-10 py-2.5">
    <Textarea
      ref="textarea"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      v-model="content"
      :placeholder="placeholder"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.meta.enter="sendWhatsAppMessage"
    />
    <div class="flex justify-end gap-2">
      <Button
        class="min-h-8"
        variant="solid"
        :label="__('Send')"
        @click="sendWhatsAppMessage"
        :disabled="isEmpty"
      />
    </div>
  </div>
</template>

<script setup>
import { createResource, Textarea } from 'frappe-ui'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  doctype: String,
})

const doc = defineModel()
const whatsapp = defineModel('whatsapp')
const rows = ref(1)
const textarea = ref(null)

const content = ref('')
const placeholder = ref(__('Type your message here...'))

const isEmpty = computed(() => {
  return !content.value || content.value === '<p></p>'
})

function show() {
  nextTick(() => textarea.value.$el.focus())
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
    message: content.value,
    to: doc.value.data.mobile_no,
    content_type: 'text',
  }
  content.value = ''
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
    onSuccess: () => nextTick(() => whatsapp.value?.reload()),
  })
}

defineExpose({ show })
</script>
