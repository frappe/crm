<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Attach'),
      size: 'xl',
    }"
  >
    <template #body-content>
      <FilesUploaderArea
        ref="filesUploaderArea"
        v-model="files"
        :doctype="doctype"
        :options="options"
      />
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div class="flex gap-2">
          <Button
            v-if="files.length"
            variant="subtle"
            :label="__('Remove all')"
            :disabled="fileUploadStarted"
            @click="removeAllFiles"
          />
          <Button
            v-if="
              filesUploaderArea?.showWebLink || filesUploaderArea?.showCamera
            "
            :label="isMobileView ? __('Back') : __('Back to file upload')"
            @click="
              () => {
                filesUploaderArea.showWebLink = false
                filesUploaderArea.showCamera = false
                filesUploaderArea.webLink = null
                filesUploaderArea.cameraImage = null
              }
            "
          >
            <template #prefix>
              <FeatherIcon name="arrow-left" class="size-4" />
            </template>
          </Button>
          <Button
            v-if="
              filesUploaderArea?.showCamera && !filesUploaderArea?.cameraImage
            "
            :label="__('Switch camera')"
            @click="() => filesUploaderArea.switchCamera()"
          />
          <Button
            v-if="filesUploaderArea?.cameraImage"
            :label="__('Retake')"
            @click="filesUploaderArea.cameraImage = null"
          />
        </div>
        <div class="flex gap-2">
          <Button
            v-if="isAllPrivate && files.length"
            variant="subtle"
            :label="__('Set all as public')"
            :disabled="fileUploadStarted"
            @click="setAllPublic"
          />
          <Button
            v-else-if="files.length"
            variant="subtle"
            :label="__('Set all as private')"
            :disabled="fileUploadStarted"
            @click="setAllPrivate"
          />
          <Button
            v-if="!filesUploaderArea?.showCamera"
            variant="solid"
            :label="__('Attach')"
            :loading="fileUploadStarted"
            :disabled="disableAttachButton"
            @click="attachFiles"
          />
          <Button
            v-if="
              filesUploaderArea?.showCamera && filesUploaderArea?.cameraImage
            "
            variant="solid"
            :label="__('Upload')"
            @click="() => filesUploaderArea.uploadViaCamera()"
          />
          <Button
            v-if="
              filesUploaderArea?.showCamera && !filesUploaderArea?.cameraImage
            "
            variant="solid"
            :label="__('Capture')"
            @click="() => filesUploaderArea.captureImage()"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FilesUploaderArea from '@/components/FilesUploader/FilesUploaderArea.vue'
import FilesUploadHandler from './filesUploaderHandler'
import { isMobileView } from '@/composables/settings'
import { toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({
      folder: 'Home/Attachments',
    }),
  },
})

const emit = defineEmits(['after'])

const show = defineModel()

const filesUploaderArea = ref(null)
const files = ref([])

const isAllPrivate = computed(() => files.value.every((a) => a.private))

function setAllPrivate() {
  files.value.forEach((file) => (file.private = true))
}

function setAllPublic() {
  files.value.forEach((file) => (file.private = false))
}

function removeAllFiles() {
  files.value = []
}

const disableAttachButton = computed(() => {
  if (filesUploaderArea.value?.showCamera) {
    return !filesUploaderArea.value.cameraImage
  }
  if (filesUploaderArea.value?.showWebLink) {
    return !filesUploaderArea.value.webLink
  }
  return !files.value.length
})

function attachFiles() {
  if (filesUploaderArea.value.showWebLink) {
    return uploadViaWebLink()
  }
  files.value.forEach((file, i) => attachFile(file, i))
}

function uploadViaWebLink() {
  let fileUrl = filesUploaderArea.value.webLink
  if (!fileUrl) {
    toast.error(__('Please enter a valid URL'))
    return
  }
  fileUrl = decodeURI(fileUrl)
  show.value = false
  return attachFile({
    fileUrl,
  })
}

const uploader = ref(null)
const fileUploadStarted = ref(false)

function attachFile(file, i) {
  const args = {
    fileObj: file.fileObj || {},
    type: file.type,
    private: file.private,
    fileUrl: file.fileUrl,
    folder: props.options.folder,
    doctype: props.doctype,
    docname: props.docname,
  }

  uploader.value = new FilesUploadHandler()

  uploader.value.on('start', () => {
    file.uploading = true
    fileUploadStarted.value = true
  })
  uploader.value.on('progress', (data) => {
    file.uploaded = data.uploaded
    file.total = data.total
  })
  uploader.value.on('error', (error) => {
    file.uploading = false
    file.errorMessage = error || 'Error Uploading File'
  })
  uploader.value.on('finish', () => {
    file.uploading = false
  })

  uploader.value
    .upload(file, args || {})
    .then(() => {
      if (i === files.value.length - 1) {
        files.value = []
        show.value = false
        fileUploadStarted.value = false
        emit('after')
      }
    })
    .catch((error) => {
      file.uploading = false
      let errorMessage = 'Error Uploading File'
      if (error?._server_messages) {
        errorMessage = JSON.parse(JSON.parse(error._server_messages)[0]).message
      } else if (error?.exc) {
        errorMessage = JSON.parse(error.exc)[0].split('\n').slice(-2, -1)[0]
      } else if (typeof error === 'string') {
        errorMessage = error
      }
      file.errorMessage = errorMessage
    })
}
</script>
