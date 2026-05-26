<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Notes" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
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
        class="group flex cursor-pointer flex-col overflow-hidden rounded-2xl border border-outline-gray-2 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
        @click="editNote(note.name)"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 pt-5">
          <div class="truncate text-[16px] font-semibold tracking-tight text-ink-gray-9">
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
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="hover:bg-surface-white"
              @click.stop
            />
          </Dropdown>
        </div>

        <!-- Image -->
        <div class="px-5 pt-4">
          <div class="h-44 overflow-hidden rounded-xl bg-surface-gray-2">
            <img
              v-if="fileUrl(note.custom_file) || extractImage(note.content)"
              :src="fileUrl(note.custom_file) || extractImage(note.content)"
              class="h-full w-full object-cover"
            />
            <div v-else class="flex h-full items-center justify-center text-ink-gray-4">
              <NoteIcon class="h-12 w-12" />
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex flex-1 flex-col px-5 pt-3">
          <div class="line-clamp-2 text-[13px] leading-6 text-ink-gray-6">
            {{ stripContent(note.content) }}
          </div>

          <!-- Location -->
          <div
            v-if="note.custom_address"
            class="mt-3 flex items-center gap-2 border-t border-outline-gray-1 pt-3 text-xs text-ink-gray-6"
          >
            <LucideMapPin class="h-3 w-3 shrink-0" />
            <span class="truncate">{{ shortAddress(note.custom_address) }}</span>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-4 flex items-center justify-between px-5 pb-5 pt-1">
          <div class="flex items-center gap-2 overflow-hidden">
            <UserAvatar :user="note.owner" size="sm" />
            <div class="truncate text-sm font-medium text-ink-gray-8">
              {{ getUser(note.owner).full_name }}
            </div>
          </div>
          <Tooltip :text="formatDate(note.modified)">
            <div class="text-sm text-ink-gray-6">
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
  <EmptyState v-else name="Notes" :icon="NoteIcon" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { usersStore } from '@/stores/users'
import { timeAgo, formatDate } from '@/utils'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { TextEditor, call, Dropdown, Tooltip, ListFooter } from 'frappe-ui'
import { ref, watch } from 'vue'

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const { showModal } = useDoctypeModal()

const notes = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// Convert private/public file path to accessible URL
function fileUrl(path) {
  if (!path) return null
  if (path.startsWith('http')) return path
  if (path.startsWith('/files/')) return path
  if (path.startsWith('/private/files/')) return path // Frappe serves private files with session cookie
  return path
}

// Extract first image src from HTML content
function extractImage(content) {
  if (!content) return null
  const match = content.match(/<img[^>]+src=["']([^"']+)["']/)
  return match ? fileUrl(match[1]) : null
}

// Strip images, SVGs, encoded SVGs, and all HTML tags — plain text only
function stripContent(content) {
  if (!content) return ''
  return content
    .replace(/<img[^>]*>/gi, '')
    .replace(/<svg[\s\S]*?<\/svg>/gi, '')
    .replace(/&lt;svg[\s\S]*?&lt;\/svg&gt;/gi, '')  // encoded SVG
    .replace(/&lt;[^&]*&gt;/g, '')                   // other encoded tags
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

// Show: "Coimbatore, Tamil Nadu" — skip pincode and country
function shortAddress(address) {
  if (!address) return ''
  const parts = address.split(',').map(p => p.trim())
  // Skip first 3 parts (Ward, Zone, Area) and last 1 part (India)
  // Keep: Coimbatore, Tamil Nadu, 641016
  return parts.slice(3, -1).join(', ')
}

watch(
  () => notes.value?.data?.page_length_count,
  (val, old_value) => {
    openNoteFromURL()
    if (!val || val === old_value) return
    updatedPageCount.value = val
  },
)

const noteCallbacks = {
  afterInsert: () => {
    notes.value.reload()
    updateOnboardingStep('create_first_note')
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

const openNoteFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const noteName = searchParams.get('open')

  if (noteName && notes.value?.data?.data) {
    const foundNote = notes.value.data.data.find(
      (note) => note.name === noteName,
    )
    if (foundNote) {
      editNote(foundNote.name)
    }
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}
</script>
