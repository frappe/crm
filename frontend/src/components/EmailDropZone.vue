<template>
  <div
    class="relative border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200"
    :class="{
      'border-gray-300': !isDragging,
      'border-blue-500 bg-blue-50': isDragging,
    }"
    @dragenter.prevent
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <div class="flex flex-col items-center justify-center space-y-2">
    <FeatherIcon name="mail" class="w-8 h-8 text-gray-400" />
      <p class="text-base text-gray-600">
        Drag and drop Email files here to add to contact
      </p>
      <p class="text-sm text-gray-500">
        Only .eml files are supported
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'
import { createToast } from '@/utils'
import FilesUploadHandler from './FilesUploader/filesUploaderHandler'

const props = defineProps({
  contactName: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['upload-complete'])

const isDragging = ref(false)
const uploader = ref(null)

onMounted(() => {
  uploader.value = new FilesUploadHandler()
})

function handleDragOver() {
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

async function handleDrop(event) {
  isDragging.value = false
  const files = event.dataTransfer?.files || []

  if (!files.length) {
    showErrorToast('No files dropped')
    return
  }

  const file = files[0]
  if (!isValidFile(file)) {
    showErrorToast('Only .eml files are allowed')
    return
  }

  try {
    await uploadFile(file)
    showSuccessToast('Email file uploaded and communication created')
    emit('upload-complete')
  } catch (error) {
    console.error('Upload error:', error)
    showErrorToast(error.message || 'Failed to upload file')
  }
}

function isValidFile(file) {
  return file.name.endsWith('.eml')
}

async function uploadFile(file) {
  try {

    const uploadResponse = await uploader.value.upload(file, {
      fileObj: file,
      folder: 'Home/Attachments',
      is_private: false,
    })

    if (!uploadResponse?.file_url) {
      throw new Error('File upload failed: No file URL returned')
    }

    const communicationResponse = await call('crm.api.doc.create_communication_from_eml', {
        file_url: uploadResponse.file_url,
        contact_name: props.contactName
      }
    )

    if (!communicationResponse) {
      throw new Error('Failed to create communication from EML file')
    }
    else if (!communicationResponse?.success) {
      throw new Error(communicationResponse?.error)
    }

    return communicationResponse.message
  } catch (error) {
    console.error('Upload error:', error)
    throw new Error(error.message || 'Failed to process email file')
  }
}

function showErrorToast(message) {
  createToast({
    title: 'Error',
    text: message,
    icon: 'x',
    iconClasses: 'text-red-500',
  })
}

function showSuccessToast(message) {
  createToast({
    title: 'Success',
    text: message,
    icon: 'check',
    iconClasses: 'text-green-500',
  })
}
</script>

<style scoped>
.border-dashed {
  border-style: dashed;
}
</style> 