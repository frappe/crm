<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    v-if="reply?.message"
    class="flex items-center justify-around gap-2 px-3 pt-2 sm:px-10"
  >
    <div
      class="mb-1 ml-13 flex-1 cursor-pointer rounded border-0 border-l-4 border-green-500 bg-surface-gray-2 p-2 text-base text-ink-gray-5"
      :class="reply.type == 'Incoming' ? 'border-green-500' : 'border-blue-400'"
    >
      <div
        class="mb-1 text-sm-bold"
        :class="
          reply.type == 'Incoming' ? 'text-ink-green-5' : 'text-ink-blue-link'
        "
      >
        {{ reply.from_name || __('You') }}
      </div>
      <div
        class="max-h-12 overflow-hidden"
        v-html="sanitizeHTML(reply.message)"
      />
    </div>

    <Button variant="ghost" icon="lucide-x" @click="reply = {}" />
  </div>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <div class="flex h-8 items-center gap-2">
      <FileUploader @success="(file) => uploadFile(file)">
        <template #default="{ openFileSelector }">
          <div class="flex items-center space-x-2">
            <Dropdown :options="uploadOptions(openFileSelector)">
              <span
                class="lucide-plus size-4.5 cursor-pointer text-ink-gray-5"
                aria-hidden="true"
              />
            </Dropdown>
          </div>
        </template>
      </FileUploader>
      <button
        v-if="!recording"
        class="lucide-mic size-4.5 cursor-pointer text-ink-gray-5"
        :title="__('Record a voice message')"
        aria-hidden="true"
        @click="startRecording"
      />
      <button
        v-else
        class="lucide-square size-4.5 cursor-pointer text-ink-red-5"
        :title="__('Stop and send')"
        aria-hidden="true"
        @click="stopRecording"
      />
      <span v-if="recording" class="text-sm tabular-nums text-ink-red-5">
        {{ recordingLabel }}
      </span>
      <IconPicker
        v-slot="{ togglePopover }"
        v-model="emoji"
        @update:modelValue="
          () => {
            content += emoji
            $refs.textareaRef.el.focus()
            capture('whatsapp_emoji_added')
          }
        "
      >
        <SmileIcon
          class="flex size-4.5 cursor-pointer rounded-sm text-2xl leading-none text-ink-gray-4"
          @click="togglePopover"
        />
      </IconPicker>
    </div>
    <Textarea
      ref="textareaRef"
      v-model="content"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      :placeholder="placeholder"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import { sanitizeHTML } from '@/utils'
import { useTelemetry } from 'frappe-ui/frappe'
import {
  createResource,
  Textarea,
  FileUploader,
  Dropdown,
  toast,
} from 'frappe-ui'
import { ref, computed, nextTick, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const whatsapp = defineModel('whatsapp', { type: Object, default: () => ({}) })
const reply = defineModel('reply', { type: Object, default: () => ({}) })

const { capture } = useTelemetry()

const rows = ref(1)
const textareaRef = ref(null)
const emoji = ref('')

const content = ref('')
const placeholder = ref(__('Type your message here...'))
const fileType = ref('')

// --- voice messages ---------------------------------------------------------
// Recorded in the browser with MediaRecorder, uploaded like any other file and
// sent as an audio message, so it lands in the same chat as everything else.
const recording = ref(false)
const recordingSeconds = ref(0)
let recorder = null
let chunks = []
let ticker = null

const recordingLabel = computed(() => {
  const seconds = recordingSeconds.value
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
})

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    toast.error(__('This browser cannot record audio'))
    return
  }
  let stream
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  } catch (e) {
    toast.error(__('Microphone access was denied'))
    return
  }
  chunks = []
  recorder = new MediaRecorder(stream)
  recorder.ondataavailable = (event) => event.data.size && chunks.push(event.data)
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop())
    clearInterval(ticker)
    recording.value = false
    if (!chunks.length) return
    await uploadRecording(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }))
  }
  recorder.start()
  recording.value = true
  recordingSeconds.value = 0
  ticker = setInterval(() => (recordingSeconds.value += 1), 1000)
  capture('whatsapp_record_audio')
}

function stopRecording() {
  if (recorder && recorder.state !== 'inactive') recorder.stop()
}

async function uploadRecording(blob) {
  const extension = (blob.type.split('/')[1] || 'webm').split(';')[0]
  const form = new FormData()
  form.append('file', blob, `voice-${Date.now()}.${extension}`)
  form.append('is_private', 1)
  form.append('doctype', props.doctype)
  form.append('docname', doc.value.name)
  try {
    const response = await fetch('/api/method/upload_file', {
      method: 'POST',
      headers: { 'X-Frappe-CSRF-Token': window.csrf_token },
      body: form,
    })
    const data = await response.json()
    const fileUrl = data?.message?.file_url
    if (!fileUrl) throw new Error('no file_url')
    whatsapp.value.attach = fileUrl
    whatsapp.value.content_type = 'audio'
    sendWhatsAppMessage()
  } catch (e) {
    toast.error(__('Could not send the voice message'))
  }
}

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
  capture('whatsapp_upload_file')
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  sendWhatsAppMessage()
  textareaRef.value.el?.blur()
  content.value = ''
  capture('whatsapp_send_message')
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    message: content.value,
    to: doc.value.mobile_no,
    attach: whatsapp.value.attach || '',
    reply_to: reply.value?.name || '',
    content_type: whatsapp.value.content_type,
  }
  content.value = ''
  fileType.value = ''
  whatsapp.value.attach = ''
  whatsapp.value.content_type = 'text'
  reply.value = {}
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
    onSuccess: () => whatsapp.value.reload(),
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to send WhatsApp message'))
    },
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
    {
      label: __('Upload Audio'),
      icon: 'mic',
      onClick: () => {
        fileType.value = 'audio'
        openFileSelector('audio/*')
      },
    },
  ]
}

onBeforeUnmount(() => {
  clearInterval(ticker)
  if (recorder && recorder.state !== 'inactive') recorder.stop()
})

watch(reply, (value) => {
  if (value?.message) {
    show()
  }
})

defineExpose({ show })
</script>
