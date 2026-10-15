<template>
  <div
    class="activity group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-5 bg-surface-gray-1 px-4 py-3 hover:bg-surface-gray-2"
  >
    <div class="flex items-center justify-between">
      <div class="flex min-w-0 items-center gap-1.5">
        <Tooltip v-if="note.pinned" :text="pinnedText">
          <span class="lucide-pin size-3.5 shrink-0 text-ink-gray-5" />
        </Tooltip>
        <div class="truncate text-lg-medium text-ink-gray-8">
          {{ note.title }}
        </div>
      </div>
      <Dropdown
        :options="[
          {
<<<<<<< HEAD
=======
            label: __('Edit'),
            icon: 'lucide-edit-2',
            onClick: () => modalRef.showNote(note),
          },
          {
            label: note.pinned ? __('Unpin') : __('Pin to top'),
            icon: note.pinned ? 'lucide-pin-off' : 'lucide-pin',
            onClick: () => togglePin(note),
          },
          {
            label: __('Copy link'),
            icon: 'lucide-link',
            onClick: () => copyToClipboard(noteLink(note.name)),
          },
          {
>>>>>>> 143e423 (feat: read-only note view, linked lead or deal, and copy link for notes)
            label: __('Delete'),
            icon: 'lucide-trash-2',
            onClick: () => deleteNote(note.name),
          },
        ]"
        class="h-6 w-6"
        @click.stop
      >
        <Button
          icon="lucide-more-horizontal"
          variant="ghost"
          class="!h-6 !w-6 hover:bg-surface-gray-2"
          @click.stop.prevent
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
    <div class="mt-1 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 truncate">
        <UserAvatar :user="note.owner" size="xs" />
        <div
          class="truncate text-sm text-ink-gray-8"
          :title="getUser(note.owner).full_name"
        >
          {{ getUser(note.owner).full_name }}
        </div>
      </div>
      <TimelineTimestamp
        :date="note.modified"
        class-name="truncate text-sm text-ink-gray-7"
      />
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { Dropdown, Tooltip, call, toast } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sanitizeHTML, copyToClipboard, timeAgo } from '@/utils'
import { useNoteView } from '@/composables/noteView'
import { computed } from 'vue'

const props = defineProps({
  note: { type: Object, default: () => ({}) },
})

const notes = defineModel({ type: Object })

const { getUser } = usersStore()
const { noteLink } = useNoteView()

const pinnedText = computed(() => {
  if (!props.note.pinned_by) return __('Pinned')
  return __('Pinned by {0} · {1}', [
    getUser(props.note.pinned_by).full_name,
    __(timeAgo(props.note.pinned_on)),
  ])
})

async function togglePin(note) {
  await call('crm.fcrm.doctype.fcrm_note.fcrm_note.set_pinned', {
    name: note.name,
    pinned: !note.pinned,
  })
  notes.value?.reload()
}

async function deleteNote(name) {
  await toast.promise(
    call('frappe.client.delete', {
      doctype: 'FCRM Note',
      name,
    }),
    {
      loading: __('Deleting note...'),
      success: __('Note deleted'),
      error: __('Failed to delete note'),
    },
  )
  notes.value?.reload()
}
</script>
