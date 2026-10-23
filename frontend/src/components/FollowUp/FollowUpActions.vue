<template>
  <div class="flex shrink-0 items-center">
    <Button
      variant="ghost"
      icon="lucide-check"
      :tooltip="__('Mark as done')"
      :loading="saving"
      @click="markDone"
    />
    <Popover v-model:open="rescheduling" side="bottom" align="end">
      <template #trigger>
        <div class="flex">
          <Button
            variant="ghost"
            icon="lucide-calendar-sync"
            :tooltip="__('Reschedule')"
          />
        </div>
      </template>
      <template #default>
        <div class="w-56 p-1.5">
          <FollowUpDates :disabled="saving" @select="reschedule" />
        </div>
      </template>
    </Popover>
  </div>
</template>
<script setup>
import FollowUpDates from '@/components/FollowUp/FollowUpDates.vue'
import { rescheduleFollowUp } from '@/composables/followUp'
import { Popover, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['change'])

const saving = ref(false)
const rescheduling = ref(false)

function markDone() {
  save(
    call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: props.task.name,
      fieldname: 'status',
      value: 'Done',
    }),
  )
}

function reschedule(dueDate) {
  save(rescheduleFollowUp(props.task, dueDate))
  rescheduling.value = false
}

async function save(request) {
  saving.value = true
  try {
    await request
    emit('change')
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not update the follow-up'))
  } finally {
    saving.value = false
  }
}
</script>
