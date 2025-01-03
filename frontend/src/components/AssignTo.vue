<template>
  <component
    v-if="assignees?.length"
    :is="assignees?.length == 1 ? 'Button' : 'div'"
  >
    <MultipleAvatar :avatars="assignees" @click="showAssignmentModal = true" />
  </component>
  <Button v-else @click="showAssignmentModal = true">
    {{ __('Assign to') }}
  </Button>
  <AssignmentModal
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="assignees"
    :doctype="doctype"
    :doc="data"
  />
</template>
<script setup>
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import { ref } from 'vue'

const props = defineProps({
  data: Object,
  doctype: String,
})

const showAssignmentModal = ref(false)
const assignees = defineModel()
</script>
