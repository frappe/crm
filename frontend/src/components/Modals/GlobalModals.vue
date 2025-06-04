<template>
  <CreateDocumentModal
    v-if="showCreateDocumentModal"
    v-model="showCreateDocumentModal"
    :doctype="createDocumentDoctype"
    :data="createDocumentData"
    @showQuickEntryModal="(dt) => openQuickEntryModal(dt)"
    @callback="(data) => createDocumentCallback(data)"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    :doctype="quickEntryDoctype"
  />
  <AboutModal v-model="showAboutModal" />
</template>
<script setup>
import CreateDocumentModal from '@/components/Modals/CreateDocumentModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AboutModal from '@/components/Modals/AboutModal.vue'
import {
  showCreateDocumentModal,
  createDocumentDoctype,
  createDocumentData,
  createDocumentCallback,
} from '@/composables/document'
import { showAboutModal } from '@/composables/modals'
import { ref } from 'vue'

const showQuickEntryModal = ref(false)
const quickEntryDoctype = ref('')

function openQuickEntryModal(dt) {
  showQuickEntryModal.value = true
  quickEntryDoctype.value = dt
}
</script>
