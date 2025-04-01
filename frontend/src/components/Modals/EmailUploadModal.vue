<script setup>
import { ref } from 'vue'
import { Dialog, call } from 'frappe-ui'
import FilesUploadHandler from '../FilesUploader/filesUploaderHandler'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
})

const emit = defineEmits(['uploaded'])
const show = defineModel()
const dialog = ref(null)
const dragActive = ref(false)
const file = ref(null)
const error = ref('')
const isUploading = ref(false)

const handleDragEnter = (e) => {
  e.preventDefault()
  dragActive.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  dragActive.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  dragActive.value = false
  const droppedFile = e.dataTransfer.files[0]
  if (droppedFile?.name.endsWith('.eml')) {
    file.value = droppedFile
    error.value = ''
  } else {
    error.value = __('Please upload a valid .eml file')
  }
}

const handleFileSelect = (e) => {
  const selectedFile = e.target.files[0]
  if (selectedFile?.name.endsWith('.eml')) {
    file.value = selectedFile
    error.value = ''
  } else {
    error.value = __('Please upload a valid .eml file')
  }
}

const uploadFile = async () => {
  if (!file.value) return
  
  isUploading.value = true
  error.value = ''
  
  try {
    const uploader = new FilesUploadHandler()
    const result = await uploader.upload(file.value, {
      fileObj: file.value,
      private: true,
      doctype: props.doctype,
      docname: props.docname
    })

    await call('crm.api.communication.create_communication_from_eml', {
      file_url: result.file_url,
      reference_name: props.docname,
      reference_doctype: props.doctype
    })
    
    show.value = false
    emit('uploaded')
  } catch (err) {
    error.value = err?.message || err?.exc || 'Error uploading file'
  } finally {
    isUploading.value = false
  }
}

const handleClose = () => {
  file.value = null
  error.value = ''
  show.value = false
}

defineExpose({ dialog })
</script>

<template>
  <Dialog v-model="show" :options="{ size: 'sm' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Upload Email') }}
          </h3>
          <Button variant="ghost" class="w-7" @click="handleClose">
            <FeatherIcon name="x" class="h-4 w-4" />
          </Button>
        </div>

        <div class="flex flex-col gap-4">
          <div
            class="flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg bg-gray-50 transition-colors"
            :class="{
              'border-black bg-black': dragActive,
              'border-gray-300': !dragActive && !file,
              'border-solid': file,
            }"
            @dragenter="handleDragEnter"
            @dragleave="handleDragLeave"
            @dragover.prevent
            @drop="handleDrop"
          >
            <div v-if="!file" class="flex flex-col items-center gap-2 text-center">
              <div class="text-gray-400">
                <FeatherIcon name="upload" class="h-6 w-6" />
              </div>
              <div class="text-gray-700 text-base">
                {{ __('Drag and drop your .eml file here') }}
              </div>
              <div class="text-gray-500 text-sm">{{ __('or') }}</div>
              <label class="inline-block px-4 py-2 rounded bg-black text-white text-sm cursor-pointer hover:bg-surface-gray-6 transition-colors">
                {{ __('Browse Files') }}
                <input
                  type="file"
                  accept=".eml"
                  class="hidden"
                  @change="handleFileSelect"
                />
              </label>
            </div>
            <div v-else class="flex items-center gap-2 w-full p-2">
              <div class="flex-1 text-gray-700 text-sm truncate">{{ file.name }}</div>
              <button
                class="flex items-center justify-center p-1 rounded text-gray-500 hover:text-gray-700 transition-colors"
                @click="file = null"
              >
                <FeatherIcon name="x" class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div v-if="error" class="text-red-500 text-sm">{{ error }}</div>
        </div>
      </div>

      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Upload')"
            :loading="isUploading"
            :disabled="!file || isUploading"
            @click="uploadFile"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
