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
  <FeedbackModal v-if="showFeedbackModal" v-model="showFeedbackModal" />
  <FieldLayoutDialogContainer />
</template>
<script setup>
import FieldLayoutDialogContainer from '@/components/Modals/FieldLayoutDialogContainer.vue'
import ChangePasswordModal from '@/components/Modals/ChangePasswordModal.vue'
import CreateDocumentModal from '@/components/Modals/CreateDocumentModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
import FeedbackModal from '@/components/Modals/FeedbackModal.vue'
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
  showFeedbackModal,
} from '@/composables/modals'
</script>
