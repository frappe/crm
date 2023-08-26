<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="openNoteModal">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="border-b"></div>
  <div v-if="notes.data" class="grid grid-cols-4 gap-4 p-5">
    <div
      v-for="note in notes.data"
      class="group flex flex-col justify-between gap-2 px-5 py-4 border rounded-lg h-52 shadow-sm hover:bg-gray-50 cursor-pointer"
      @click="openNoteModal(note)"
    >
      <div class="flex items-center justify-between">
        <div class="text-lg font-medium truncate">
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
      <div
        class="flex-1 text-base leading-5 text-gray-700 overflow-hidden"
        v-html="note.content"
      />
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <UserAvatar :user="note.owner" size="xs" />
          <div class="text-sm text-gray-800">
            {{ note.owner }}
          </div>
        </div>
        <div class="text-sm text-gray-700">
          {{ timeAgo(note.modified) }}
        </div>
      </div>
    </div>
  </div>
  <Dialog
    v-model="showNoteModal"
    :options="{ size: '4xl' }"
    @close="updateNote"
  >
    <template #body-title><div></div></template>
    <template #body-content>
      <div
        class="flex flex-col gap-2 px-20 mt-5 mb-10 min-h-[400px] max-h-[500px] overflow-auto"
      >
        <TextInput
          ref="title"
          type="text"
          class="!text-[30px] !h-10 !font-semibold bg-white border-none hover:bg-white focus:!shadow-none focus-visible:!ring-0"
          v-model="currentNote.title"
          placeholder="Untitled note"
        />
        <TextEditor
          ref="content"
          editor-class="!prose-sm max-w-none p-2 overflow-auto focus:outline-none"
          :bubbleMenu="true"
          :content="currentNote.content"
          @change="(val) => (currentNote.content = val)"
          placeholder="Type something and press enter"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { timeAgo } from '@/utils'
import {
  FeatherIcon,
  Button,
  createListResource,
  TextEditor,
  TextInput,
  call,
  Dropdown,
} from 'frappe-ui'
import { nextTick, ref } from 'vue'

const list = {
  title: 'Notes',
  plural_label: 'Notes',
  singular_label: 'Note',
}

const showNoteModal = ref(false)
const currentNote = ref(null)
const oldNote = ref(null)
const title = ref(null)
const content = ref(null)

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

const openNoteModal = (note) => {
  let noteCopy = { ...note }
  oldNote.value = note
  currentNote.value = noteCopy
  showNoteModal.value = true

  nextTick(() => title.value.el.focus())
}

async function updateNote() {
  if (
    currentNote.value.title === oldNote.value.title &&
    currentNote.value.content === oldNote.value.content
  ) {
    return
  }
  currentNote.value.content = content.value?.editor.getHTML()

  if (currentNote.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: currentNote.value.name,
      fieldname: currentNote.value,
    })
    if (d.name) {
      notes.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Note',
        title: currentNote.value.title,
        content: currentNote.value.content,
      },
    })
    if (d.name) {
      notes.reload()
    }
  }
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Note',
    name,
  })
  notes.reload()
}
</script>
