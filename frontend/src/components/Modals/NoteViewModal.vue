<template>
  <Dialog v-model:open="show" size="2xl" bare>
    <template #default>
      <div class="px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-4 flex items-start justify-between gap-4">
          <Dialog.Title as-child>
            <h3 class="text-3xl-semibold leading-8 text-ink-gray-9">
              {{ doc.title }}
            </h3>
          </Dialog.Title>
          <div class="flex shrink-0 items-center gap-1">
            <Button
              v-if="onEdit"
              :label="__('Edit')"
              iconLeft="lucide-edit-2"
              @click="edit"
            />
            <Button
              variant="ghost"
              class="w-7"
              :tooltip="__('Copy link')"
              icon="lucide-link"
              @click="copyToClipboard(noteLink(doc.name))"
            />
            <Dialog.Close as-child>
              <Button
                :aria-label="__('Close')"
                variant="ghost"
                class="w-7"
                icon="lucide-x"
              />
            </Dialog.Close>
          </div>
        </div>
        <div v-if="doc.owner" class="mb-5 flex items-center gap-2 text-p-sm">
          <UserAvatar :user="doc.owner" size="xs" />
          <span class="text-ink-gray-8">
            {{ getUser(doc.owner).full_name }}
          </span>
          <span class="text-ink-gray-5">·</span>
          <Tooltip :text="formatDate(doc.modified)">
            <span class="text-ink-gray-5">{{ __(timeAgo(doc.modified)) }}</span>
          </Tooltip>
          <template v-if="linkedRoute(doc)">
            <span class="text-ink-gray-5">·</span>
            <router-link
              :to="linkedRoute(doc)"
              class="truncate text-ink-gray-5 hover:text-ink-gray-8 hover:underline"
              @click="show = false"
            >
              {{ linkedLabel(doc) }}
            </router-link>
          </template>
        </div>
        <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          v-if="doc.content"
          class="prose-f max-h-[60vh] overflow-y-auto text-ink-gray-8 [&>*:first-child]:mt-0"
          v-html="sanitizeHTML(doc.content)"
        />
        <!-- eslint-enable vue/no-v-html -->
        <div v-else-if="loaded" class="text-p-base text-ink-gray-5">
          {{ __('This note is empty.') }}
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import UserAvatar from '@/components/UserAvatar.vue'
import { useNoteView, type NoteRef } from '@/composables/noteView'
import { usersStore } from '@/stores/users'
import { copyToClipboard, formatDate, sanitizeHTML, timeAgo } from '@/utils'
import { Dialog, Tooltip, call } from 'frappe-ui'
import { ref, watch } from 'vue'

const {
  show,
  note,
  onEdit,
  noteLink,
  loadLinkedTitles,
  linkedRoute,
  linkedLabel,
} = useNoteView()
const { getUser } = usersStore()

const doc = ref<NoteRef & { owner?: string; modified?: string }>({ name: '' })
const loaded = ref(false)

// a shared link only carries the note name, so load the rest
watch(
  note,
  async (n: NoteRef | null) => {
    doc.value = n || { name: '' }
    loaded.value = Boolean(n?.owner)
    if (n?.name && !n.owner) {
      doc.value = await call('frappe.client.get', {
        doctype: 'FCRM Note',
        name: n.name,
      })
      loaded.value = true
    }
    loadLinkedTitles([doc.value])
  },
  { immediate: true },
)

function edit() {
  show.value = false
  onEdit.value?.()
}
</script>
