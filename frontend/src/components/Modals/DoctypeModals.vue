<template>
  <DoctypeModal
    v-if="doctypeModal.show.value"
    v-model="doctypeModal.show.value"
    :doctypeTitle="doctypeModal.title.value"
    :doctype="doctypeModal.doctype.value"
    :docname="doctypeModal.name.value"
    :defaults="doctypeModal.defaults.value"
    @afterInsert="(d) => doctypeModal.triggerCallback('afterInsert', d)"
    @afterUpdate="(d) => doctypeModal.triggerCallback('afterUpdate', d)"
  />
</template>
<script setup>
import DoctypeModal from '@/components/Modals/DoctypeModal.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const doctypeModal = useDoctypeModal()
const route = useRoute()

// The page's keyed router-view is replaced on fullPath changes.
watch(() => route.fullPath, doctypeModal.closeModal, { flush: 'sync' })
</script>
