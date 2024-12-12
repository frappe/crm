<template>
  <div
    class="activity group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-md bg-gray-50 px-4 py-3 hover:bg-gray-100"
  >
    <div class="flex items-center justify-between">
      <div class="truncate text-lg font-medium">
        {{ note.title }}
      </div>
      <Dropdown
        :options="[
          {
            label: __('Delete'),
            icon: 'trash-2',
            onClick: () => deleteNote(note.name),
          },
        ]"
        @click.stop
        class="h-6 w-6"
      >
        <Button
          icon="more-horizontal"
          variant="ghosted"
          class="!h-6 !w-6 hover:bg-gray-100"
        />
      </Dropdown>
    </div>
    <TextEditor
      v-if="note.content"
      :content="note.content"
      :editable="false"
      editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
      class="flex-1 overflow-hidden"
    />



    <div v-if="attachments && attachments.length" class="overflow-auto">
      <!-- <ul class="w-full rounded-lg mt-2 mb-3 text-blue-800">
      <li class="mb-1">
        <AttachmentIcon></AttachmentIcon>
      <span class="ml-2 truncate" title="Test with a very really long name (resize the browser to see it truncate)">Test with a very really long name (resize the browser to see it truncate)</span>
      </li>
      </ul> -->
      <ul class="w-full rounded-lg mt-2 mb-3 text-blue-800">
      <li  class="mb-1 text-sm"
        v-for="attachment in attachments" >
        <a :href="attachment.file_name" target="_blank"  class="w-fill flex p-3 pl-3 bg-gray-100 hover:bg-gray-200 rounded-lg">
        <AttachmentIcon class="flex-none w-4 h-full"></AttachmentIcon>

        <span class="ml-2 truncate"  target="_blank">{{ attachment.file_name }}</span>
        </a>
    </li>
    </ul>
    </div>




    <div class="mt-1 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 truncate">
        <UserAvatar :user="note.owner" size="xs" />
        <div
          class="truncate text-sm text-gray-800"
          :title="getUser(note.owner).full_name"
        >
          {{ getUser(note.owner).full_name }}
        </div>
      </div>
      <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
        <div class="truncate text-sm text-gray-700">
          {{ __(timeAgo(note.modified)) }}
        </div>
      </Tooltip>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { Tooltip, Dropdown, TextEditor, FileUploader , createResource, call} from 'frappe-ui'
import { usersStore } from '@/stores/users'
import AttachmentItem from '@/components/AttachmentItem.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'

import {  onMounted , ref} from 'vue'

const props = defineProps({
  note: Object,
})

const notes = defineModel()
const attachments = ref([])

const { getUser } = usersStore()

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'FCRM Note',
    name,
  })
  notes.value.reload()
}

onMounted(() => {
  createResource({
    params: {
      note_name: props.note?.name,
    },
    auto: true,
    url: 'crm.fcrm.doctype.fcrm_note.api.get_attachments_from_note',
    transform: (data) => {
    data.forEach((item) => {
      attachments.value.push(item);
    });
    },
  });
})

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment)
}
</script>