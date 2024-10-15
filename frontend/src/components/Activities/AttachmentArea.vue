<template>
  <div
    class="flex justify-between gap-2 border rounded text-base px-3 py-2 cursor-pointer"
    @click="openFile"
  >
    <div class="flex gap-2 truncate">
      <div
        class="size-11 rounded overflow-hidden flex-shrink-0 flex justify-center items-center"
        :class="{ border: !isImage(attachment.file_type) }"
      >
        <img
          v-if="isImage(attachment.file_type)"
          class="size-full object-cover"
          :src="attachment.file_url"
          :alt="attachment.file_name"
        />
        <component v-else class="size-4" :is="fileIcon(attachment.file_type)" />
      </div>
      <div class="flex flex-col justify-center gap-1 truncate">
        <div class="text-base text-gray-800 truncate">
          {{ attachment.file_name }}
        </div>
        <div class="mb-1 text-sm text-gray-600">
          {{ convertSize(attachment.file_size) }}
        </div>
      </div>
    </div>
    <div class="flex flex-col items-end gap-2 flex-shrink-0">
      <Tooltip :text="dateFormat(attachment.creation, dateTooltipFormat)">
        <div class="text-sm text-gray-600">
          {{ __(timeAgo(attachment.creation)) }}
        </div>
      </Tooltip>
      <div class="flex gap-1">
        <Tooltip
          :text="attachment.is_private ? __('Make public') : __('Make private')"
        >
          <Button
            class="!size-5"
            @click.stop="togglePrivate(attachment.name, attachment.is_private)"
          >
            <FeatherIcon
              :name="attachment.is_private ? 'lock' : 'unlock'"
              class="size-3 text-gray-700"
            />
          </Button>
        </Tooltip>
        <Tooltip :text="__('Delete attachment')">
          <Button
            class="!size-5"
            @click.stop="() => deleteAttachment(attachment.name)"
          >
            <FeatherIcon name="trash-2" class="size-3 text-gray-700" />
          </Button>
        </Tooltip>
      </div>
    </div>
  </div>
</template>
<script setup>
import FileAudioIcon from '@/components/Icons/FileAudioIcon.vue'
import FileTextIcon from '@/components/Icons/FileTextIcon.vue'
import FileVideoIcon from '@/components/Icons/FileVideoIcon.vue'
import { globalStore } from '@/stores/global'
import { call, Tooltip } from 'frappe-ui'
import {
  dateFormat,
  timeAgo,
  dateTooltipFormat,
  convertSize,
  isImage,
} from '@/utils'

const props = defineProps({
  attachment: Object,
})

const emit = defineEmits(['reload'])

const { $dialog } = globalStore()

function openFile() {
  window.open(props.attachment.file_url, '_blank')
}

function togglePrivate(fileName, isPrivate) {
  let changeTo = isPrivate ? __('public') : __('private')
  let title = __('Make attachment {0}', [changeTo])
  let message = __('Are you sure you want to make this attachment {0}?', [
    changeTo,
  ])
  $dialog({
    title,
    message,
    actions: [
      {
        label: __('Make {0}', [changeTo]),
        variant: 'solid',
        onClick: async (close) => {
          await call('frappe.client.set_value', {
            doctype: 'File',
            name: fileName,
            fieldname: {
              is_private: !isPrivate,
            },
          })
          emit('reload')
          close()
        },
      },
    ],
  })
}

function deleteAttachment(fileName) {
  $dialog({
    title: __('Delete attachment'),
    message: __('Are you sure you want to delete this attachment?'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (close) => {
          await call('frappe.client.delete', {
            doctype: 'File',
            name: fileName,
          })
          emit('reload')
          close()
        },
      },
    ],
  })
}

function fileIcon(type) {
  if (!type) return FileTextIcon
  let audioExtentions = ['wav', 'mp3', 'ogg', 'flac', 'aac']
  let videoExtentions = ['mp4', 'avi', 'mkv', 'flv', 'mov']
  if (audioExtentions.includes(type.toLowerCase())) {
    return FileAudioIcon
  } else if (videoExtentions.includes(type.toLowerCase())) {
    return FileVideoIcon
  }
  return FileTextIcon
}
</script>
