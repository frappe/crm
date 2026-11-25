<template>
  <CreateDocumentModal
    v-if="showCreateDocumentModal"
    v-model="showCreateDocumentModal"
    :doctype="createDocumentDoctype"
    :data="createDocumentData"
    @callback="(data) => createDocumentCallback(data)"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    v-bind="quickEntryProps"
  />
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
  <AboutModal v-model="showAboutModal" />
  <NoteViewModal v-if="showNoteView" />
  <MentionHoverCard />
  <FieldLayoutDialogContainer />
  <CommandPalette />
</template>
<script setup>
import CommandPalette from '@/components/CommandPalette/CommandPalette.vue'
import FieldLayoutDialogContainer from '@/components/Modals/FieldLayoutDialogContainer.vue'
import ChangePasswordModal from '@/components/Modals/ChangePasswordModal.vue'
import CreateDocumentModal from '@/components/Modals/CreateDocumentModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
import NoteViewModal from '@/components/Modals/NoteViewModal.vue'
import MentionHoverCard from '@/components/MentionHoverCard.vue'
import { useNoteView } from '@/composables/noteView'
import {
  showCreateDocumentModal,
  createDocumentDoctype,
  createDocumentData,
  createDocumentCallback,
} from '@/composables/document'
import {
  showQuickEntryModal,
  quickEntryProps,
  showAboutModal,
  showChangePasswordModal,
} from '@/composables/modals'

const { show: showNoteView } = useNoteView()
</script>
