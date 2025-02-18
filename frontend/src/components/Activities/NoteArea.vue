<template>
  <div
    class="activity group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-md bg-gray-50 px-4 py-3 hover:bg-surface-gray-2"
  >
    <div class="flex items-center justify-between">
      <div class="truncate text-lg font-medium">
        {{ note.custom_title }}
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
        <Button icon="more-horizontal" variant="ghosted" class="!h-6 !w-6 hover:bg-surface-gray-2" />
      </Dropdown>
    </div>
    <TextEditor
      v-if="note.note"
      :content="note.note"
      :editable="false"
      editor-class="!prose-sm max-w-none !text-sm text-ink-gray-5 focus:outline-none"
      class="flex-1 overflow-hidden"
    />
    <div class="mt-1 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 truncate">
        <UserAvatar :user="note.owner" size="xs" />
        <div class="truncate text-sm text-ink-gray-8" :title="getUser(note.owner).full_name">
          {{ getUser(note.owner).full_name }}
        </div>
      </div>
      <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
        <div class="truncate text-sm text-ink-gray-7">
          {{ __(timeAgo(note.modified)) }}
        </div>
      </Tooltip>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { Tooltip, Dropdown, TextEditor, call } from 'frappe-ui'
import { usersStore } from '@/stores/users'

const props = defineProps({
  note: Object,
})

const notes = defineModel()

const { getUser } = usersStore()

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Note',
    name,
  })
  notes.value?.reload()
}
</script>
