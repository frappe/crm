<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="createNote">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div
    v-if="notes.data?.length"
    class="grid grid-cols-4 gap-4 overflow-y-auto p-5"
  >
    <div
      v-for="note in notes.data"
      class="group flex h-56 cursor-pointer flex-col justify-between gap-2 rounded-lg border px-5 py-4 shadow-sm hover:bg-gray-50"
      @click="editNote(note)"
    >
      <div class="flex items-center justify-between">
        <div class="truncate text-lg font-medium">
          {{ note.title }}
        </div>
        <Dropdown
          :options="[
            {
              icon: 'trash-2',
              label: 'Delete',
              onClick: () => deleteNote(note.name),
            },
          ]"
          @click.stop
        >
          <Button
            icon="more-horizontal"
            variant="ghosted"
            class="hover:bg-white"
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
      <div class="mt-2 flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <UserAvatar :user="note.owner" size="xs" />
          <div class="text-sm text-gray-800">
            {{ getUser(note.owner).full_name }}
          </div>
        </div>
        <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
          <div class="text-sm text-gray-700">
            {{ timeAgo(note.modified) }}
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
  <div v-else class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <NoteIcon class="h-10 w-10" />
      <span>No Notes Found</span>
      <Button label="Create" @click="createNote">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <NoteModal
    v-model="showNoteModal"
    v-model:reloadNotes="notes"
    :note="currentNote"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import {
  createListResource,
  TextEditor,
  call,
  Dropdown,
  Tooltip,
  Breadcrumbs,
} from 'frappe-ui'
import { ref } from 'vue'
import { usersStore } from '@/stores/users'

const { getUser } = usersStore()

const list = {
  title: 'Notes',
  plural_label: 'Notes',
  singular_label: 'Note',
}

const breadcrumbs = [{ label: list.title, route: { name: 'Notes' } }]

const showNoteModal = ref(false)
const currentNote = ref(null)

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  cache: 'Notes',
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: {},
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

function createNote() {
  currentNote.value = {
    title: '',
    content: '',
  }
  showNoteModal.value = true
}

function editNote(note) {
  currentNote.value = note
  showNoteModal.value = true
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Note',
    name,
  })
  notes.reload()
}
</script>
