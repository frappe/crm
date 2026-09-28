<template>
  <div class="flex flex-col gap-4">
    <div
      class="flex h-[260px] items-center justify-center rounded-md border border-dashed border-outline-gray-3 bg-surface-gray-1"
      :class="{ 'border-outline-gray-5 bg-surface-gray-2': dragging }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <div v-if="uploading" class="w-4/5 rounded-md border bg-surface-base p-3">
        <div class="font-medium text-ink-gray-9">{{ fileName }}</div>
        <div class="mt-3 h-1 w-full rounded-full bg-surface-gray-2">
          <div
            class="h-1 rounded-full bg-surface-gray-9 transition-all duration-300"
            :style="{ width: `${progress}%` }"
          />
        </div>
      </div>
      <div v-else class="w-4/5 text-center">
        <LucideUploadCloud class="mx-auto mb-2.5 size-6 text-ink-gray-6" />
        <input
          ref="fileInput"
          type="file"
          accept=".csv,text/csv"
          class="hidden"
          @change="onSelect"
        />
        <p class="leading-5 text-ink-gray-9">
          {{ __('Drag and drop a CSV file, or') }}
          <button
            type="button"
            class="font-semibold hover:underline"
            @click="fileInput.click()"
          >
            {{ __('choose one from your device') }}
          </button>
        </p>
        <p class="mt-1 text-sm text-ink-gray-5">
          {{ __('The first row should contain column names.') }}
        </p>
      </div>
    </div>
    <ErrorMessage v-if="error" :message="error" />
    <div class="flex items-center justify-between">
      <Button variant="ghost" :label="__('Cancel')" @click="emit('cancel')" />
      <Button variant="ghost" :link="templateUrl">
        <template #prefix><LucideDownload class="size-4" /></template>
        {{ __('Download CSV template') }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import LucideUploadCloud from '~icons/lucide/upload-cloud'
import LucideDownload from '~icons/lucide/download'
import { Button, ErrorMessage, FileUploadHandler } from 'frappe-ui'
import { computed, ref } from 'vue'

const emit = defineEmits(['uploaded', 'cancel'])

const TEMPLATE_FIELDS = [
  'first_name',
  'last_name',
  'email',
  'mobile_no',
  'organization',
  'job_title',
  'website',
  'source',
]

const fileInput = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const progress = ref(0)
const fileName = ref('')
const error = ref('')

const templateUrl = computed(() => {
  const params = new URLSearchParams({
    doctype: 'CRM Lead',
    export_fields: JSON.stringify({ 'CRM Lead': TEMPLATE_FIELDS }),
    export_records: 'blank_template',
    file_type: 'CSV',
  })
  return `/api/method/frappe.core.doctype.data_import.data_import.download_template?${params}`
})

function onDrop(event) {
  dragging.value = false
  upload(event.dataTransfer?.files?.[0])
}

function onSelect(event) {
  upload(event.target.files?.[0])
  event.target.value = ''
}

async function upload(file) {
  if (!file) return
  error.value = ''
  if (!file.name.toLowerCase().endsWith('.csv')) {
    error.value = __('Please upload a CSV file.')
    return
  }
  fileName.value = file.name
  uploading.value = true
  progress.value = 0
  const uploader = new FileUploadHandler()
  uploader.on('progress', ({ uploaded, total }) => {
    progress.value = total ? Math.floor((uploaded / total) * 100) : 0
  })
  try {
    const uploaded = await uploader.upload(file, { private: true })
    emit('uploaded', uploaded.file_url)
  } catch (e) {
    error.value = e.message || __('Could not upload the file.')
  } finally {
    uploading.value = false
  }
}
</script>
