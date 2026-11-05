<template>
  <Button
    v-if="item.kind === 'follow_up'"
    :label="__('Mark done')"
    :loading="saving"
    @click="markDone"
  />
  <FollowUpPopover
    v-else-if="item.kind === 'no_next_step'"
    :doctype="item.doctype"
    :docname="item.name"
    :title="__('Follow up with {0}', [recordTitle(item)])"
    @created="refreshHome"
  >
    <Button :label="__('Follow up')" />
  </FollowUpPopover>
  <template v-else-if="item.kind === 'client'">
    <Button :label="__('Reassign')" @click="assigning = true" />
    <AssignmentModal
      v-if="assigning"
      v-model="assigning"
      v-model:assignees="assignees"
      :docs="new Set([item.name])"
      :doctype="item.doctype"
      @reload="refreshHome"
    />
  </template>
  <Button
    v-else
    :label="briefActionLabel(item)"
    :route="briefActionRoute(item)"
  />
</template>
<script setup>
import FollowUpPopover from '@/components/FollowUp/FollowUpPopover.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import { refreshHome } from '@/composables/homeWidget'
import { briefActionLabel, briefActionRoute } from '@/utils/brief'
import { recordTitle } from '@/utils/home'
import { call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  item: { type: Object, required: true },
})

const saving = ref(false)
const assigning = ref(false)
const assignees = ref([])

async function markDone() {
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: props.item.name,
      fieldname: 'status',
      value: 'Done',
    })
    refreshHome()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not update the follow-up'))
  } finally {
    saving.value = false
  }
}
</script>
