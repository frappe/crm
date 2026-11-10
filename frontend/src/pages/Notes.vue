<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Notes" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="lucide-plus"
        @click="createNote"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="notes"
    v-model:loadMore="loadMore"
    v-model:updatedPageCount="updatedPageCount"
    doctype="FCRM Note"
    :options="{
      hideColumnsButton: true,
      defaultViewName: __('Notes View'),
    }"
  />
  <div class="flex-1 overflow-y-auto">
    <div
      v-if="notes.data?.data?.length"
      class="grid grid-cols-1 gap-2 px-3 pb-2 sm:grid-cols-4 sm:gap-4 sm:px-5 sm:pb-3"
    >
      <div
        v-for="note in notes.data.data"
        :key="note.name"
        class="group flex h-56 cursor-pointer flex-col justify-between gap-2 rounded-6 border px-5 py-4 shadow-sm hover:bg-surface-sidebar"
        @click="openNote(note, { edit: () => editNote(note.name) })"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex min-w-0 flex-col gap-1">
            <div class="truncate text-lg-medium text-ink-gray-9">
              {{ note.title }}
            </div>
            <router-link
              v-if="linkedRoute(note)"
              :to="linkedRoute(note)"
              class="truncate text-sm text-ink-gray-5 hover:text-ink-gray-8 hover:underline"
              @click.stop
            >
              {{ linkedLabel(note) }}
            </router-link>
          </div>
          <Dropdown
            :options="[
              {
                label: __('Edit'),
                icon: 'lucide-edit-2',
                onClick: () => editNote(note.name),
              },
              {
                label: __('Copy link'),
                icon: 'lucide-link',
                onClick: () => copyNoteLink(note.name),
              },
              {
                label: __('Delete'),
                icon: 'lucide-trash-2',
                onClick: () => deleteNote(note.name),
              },
            ]"
          >
            <Button
              icon="lucide-more-horizontal"
              variant="ghost"
              class="hover:bg-surface-base"
              @click.stop
            />
          </Dropdown>
        </div>
        <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          v-if="note.content"
          class="prose-f prose-sm text-p-sm max-w-none text-ink-gray-5 flex-1 overflow-hidden prose-headings:my-1 prose-headings:text-p-sm prose-headings:font-medium prose-headings:text-ink-gray-7 [&>*:first-child]:mt-0"
          v-html="sanitizeHTML(note.content)"
        />
        <!-- eslint-enable vue/no-v-html -->
        <div class="mt-2 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <UserAvatar :user="note.owner" size="xs" />
            <div class="text-sm text-ink-gray-8">
              {{ getUser(note.owner).full_name }}
            </div>
          </div>
          <Tooltip :text="formatDate(note.modified)">
            <div class="text-sm text-ink-gray-7">
              {{ __(timeAgo(note.modified)) }}
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
  </div>
  <ListFooter
    v-if="notes.data?.data?.length"
    v-model="notes.data.page_length_count"
    class="border-t px-3 py-2 sm:px-5"
    :options="{
      rowCount: notes.data.row_count,
      totalCount: notes.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <EmptyState
    v-else
    name="Notes"
    :icon="NoteIcon"
    :title="__('No notes yet')"
    :description="
      __(
        'Notes keep what you learned on a call or in a meeting next to the lead or deal it belongs to.',
      )
    "
    :filtered="!!Object.keys(notes.params?.filters || {}).length"
    docsLink="https://docs.frappe.io/crm/note"
    @create="createNote"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useNoteView } from '@/composables/noteView'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { usersStore } from '@/stores/users'
import { timeAgo, formatDate, sanitizeHTML, copyToClipboard } from '@/utils'
import { useTelemetry } from '@framework/ui/telemetry'
import { call, Dropdown, Tooltip } from 'frappe-ui'
import { ListFooter } from 'frappe-ui/experimental'
import { ref, watch, onMounted } from 'vue'

const { getUser } = usersStore()
const { capture } = useTelemetry()

const { showModal } = useDoctypeModal()
const { openNote, noteLink, loadLinkedTitles, linkedRoute, linkedLabel } =
  useNoteView()

const notes = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

watch(
  () => notes.value?.data?.page_length_count,
  (val, old_value) => {
    if (!val || val === old_value) return
    updatedPageCount.value = val
  },
)

watch(
  () => notes.value?.data?.data,
  (rows) => loadLinkedTitles(rows),
)

function copyNoteLink(name) {
  copyToClipboard(noteLink(name))
}

const noteCallbacks = {
  afterInsert: () => {
    notes.value.reload()
    capture('note_created')
  },
  afterUpdate: () => {
    notes.value.reload()
    capture('note_updated')
  },
}

function createNote() {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

function editNote(noteName) {
  showModal({
    name: noteName,
    doctype: 'FCRM Note',
    title: 'Note',
    callbacks: noteCallbacks,
  })
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'FCRM Note',
    name,
  })
  notes.value.reload()
}

// open a shared note link, even when the note is not on the loaded page
onMounted(() => {
  const searchParams = new URLSearchParams(window.location.search)
  const noteName = searchParams.get('open')
  if (!noteName) return
  openNote({ name: noteName }, { edit: () => editNote(noteName) })
  searchParams.delete('open')
  window.history.replaceState(null, '', window.location.pathname)
})
</script>
