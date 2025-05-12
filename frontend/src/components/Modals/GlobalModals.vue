<template>
  <CreateDocumentModal
    v-if="showCreateDocumentModal"
    v-model="showCreateDocumentModal"
    :doctype="createDocumentDoctype"
    :data="createDocumentData"
    @showQuickEntryModal="(dt) => openQuickEntryModal(dt)"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    :doctype="quickEntryDoctype"
  />
</template>
<script setup>
import CreateDocumentModal from '@/components/Modals/CreateDocumentModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import {
  showCreateDocumentModal,
  createDocumentDoctype,
  createDocumentData,
} from '@/composables/document'
import { ref } from 'vue'

const showQuickEntryModal = ref(false)
const quickEntryDoctype = ref('')

function openQuickEntryModal(dt) {
  showQuickEntryModal.value = true
  quickEntryDoctype.value = dt
}
</script>
