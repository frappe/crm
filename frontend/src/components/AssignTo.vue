<template>
  <NestedPopover>
    <template #target>
      <component
        v-if="assignees?.length"
        :is="assignees?.length == 1 ? 'Button' : 'div'"
      >
        <MultipleAvatar :avatars="assignees" />
      </component>
      <Button v-else :label="__('Assign to')" />
    </template>
    <template #body="{ open }">
      <AssignToBody
        v-show="open"
        v-model="assignees"
        :doc="data"
        :doctype="doctype"
        :open="open"
      />
    </template>
  </NestedPopover>
</template>
<script setup>
import NestedPopover from '@/components/NestedPopover.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AssignToBody from '@/components/AssignToBody.vue'

const props = defineProps({
  data: Object,
  doctype: String,
})

const assignees = defineModel()
</script>
