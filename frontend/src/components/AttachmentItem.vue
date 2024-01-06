<template>
  <span>
    <a :href="isShowable ? null : url" target="_blank">
      <Button
        :label="label"
        theme="gray"
        variant="outline"
        @click="toggleDialog()"
      >
        <template #prefix>
          <component :is="getIcon()" class="h-4 w-4" />
        </template>
        <template #suffix>
          <slot name="suffix" />
        </template>
      </Button>
    </a>
    <Dialog
      v-model="showDialog"
      :options="{
        title: label,
        size: '4xl',
      }"
    >
      <template #body-content>
        <div
          v-if="isText"
          class="prose prose-sm max-w-none whitespace-pre-wrap"
        >
          {{ content }}
        </div>
        <img v-if="isImage" :src="url" class="m-auto rounded border" />
      </template>
    </Dialog>
  </span>
</template>

<script setup>
import { ref } from 'vue'
import mime from 'mime'
import FileTypeIcon from '@/components/Icons/FileTypeIcon.vue'
import FileImageIcon from '@/components/Icons/FileImageIcon.vue'
import FileTextIcon from '@/components/Icons/FileTextIcon.vue'
import FileSpreadsheetIcon from '@/components/Icons/FileSpreadsheetIcon.vue'
import FileIcon from '@/components/Icons/FileIcon.vue'

const props = defineProps({
  label: {
    type: String,
    default: null,
  },
  url: {
    type: String,
    default: null,
  },
})

const showDialog = ref(false)
const mimeType = mime.getType(props.label) || ''
const isImage = mimeType.startsWith('image/')
const isPdf = mimeType === 'application/pdf'
const isSpreadsheet = mimeType.includes('spreadsheet')
const isText = mimeType === 'text/plain'
const isShowable = props.url && (isText || isImage)
const content = ref('')

function getIcon() {
  if (isText) return FileTypeIcon
  else if (isImage) return FileImageIcon
  else if (isPdf) return FileTextIcon
  else if (isSpreadsheet) return FileSpreadsheetIcon
  else return FileIcon
}

function toggleDialog() {
  if (!isShowable) return
  if (isText) {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)))
  }
  showDialog.value = !showDialog.value
}
</script>
