<template>
  <div class="flex items-end gap-2 px-10 py-2.5">
    <div class="flex h-8 items-center">
      <FileUploader @success="(file) => uploadFile(file)">
        <template v-slot="{ file, progress, uploading, openFileSelector }">
          <div class="flex items-center space-x-2">
            <Dropdown
              v-bind="{ open }"
              :options="uploadOptions(openFileSelector)"
            >
              <FeatherIcon
                name="plus"
                class="size-4.5 cursor-pointer text-gray-600"
              />
            </Dropdown>
          </div>
        </template>
      </FileUploader>
    </div>
    <Textarea
      ref="textarea"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      v-model="content"
      :placeholder="placeholder"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.enter="(e) => sendTextMessage(e)"
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
import { createResource, Textarea, FileUploader, Dropdown } from 'frappe-ui'
import FeatherIcon from 'frappe-ui/src/components/FeatherIcon.vue'
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
const fileType = ref('')

const isEmpty = computed(() => {
  return !content.value || content.value === '<p></p>'
})

function show() {
  nextTick(() => textarea.value.$el.focus())
}

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  sendWhatsAppMessage()
  textarea.value.$el.blur()
  content.value = ''
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
    message: content.value,
    to: doc.value.data.mobile_no,
    attach: whatsapp.value.attach || '',
    content_type: whatsapp.value.content_type,
  }
  content.value = ''
  fileType.value = ''
  whatsapp.value.attach = ''
  whatsapp.value.content_type = 'text'
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
    onSuccess: () => nextTick(() => whatsapp.value?.reload()),
  })
}

function uploadOptions(openFileSelector) {
  return [
    {
      label: __('Upload Document'),
      icon: 'file',
      onClick: () => {
        fileType.value = 'document'
        openFileSelector()
      },
    },
    {
      label: __('Upload Image'),
      icon: 'image',
      onClick: () => {
        fileType.value = 'image'
        openFileSelector('image/*')
      },
    },
    {
      label: __('Upload Video'),
      icon: 'video',
      onClick: () => {
        fileType.value = 'video'
        openFileSelector('video/*')
      },
    },
  ]
}

defineExpose({ show })
</script>
