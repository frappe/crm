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
        v-model="files"
        :doctype="doctype"
        :options="options"
      />
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button
            v-if="files.length"
            variant="subtle"
            :label="__('Remove all')"
            :disabled="fileUploadStarted"
            @click="removeAllFiles"
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
            variant="solid"
            :loading="fileUploadStarted"
            :disabled="!files.length"
            @click="attachFiles"
            :label="__('Attach')"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FilesUploaderArea from '@/components/FilesUploader/FilesUploaderArea.vue'
import FilesUploadHandler from './filesUploaderHandler'
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

const show = defineModel()
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

function attachFiles() {
  files.value.forEach((file, i) => attachFile(file, i))
}

const uploader = ref(null)
const fileUploadStarted = ref(false)

function attachFile(file, i) {
  const args = {
    file: file?.fileObj || {},
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
