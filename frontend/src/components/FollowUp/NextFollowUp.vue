<template>
  <div
    v-if="task"
    class="flex items-center gap-1.5 border-b px-5 py-2 text-base text-ink-gray-8"
  >
    <button
      type="button"
      class="flex min-w-0 flex-1 items-center gap-1.5 text-left"
      @click="emit('open', task)"
    >
      <span class="shrink-0 text-ink-gray-5">{{ __('Next:') }}</span>
      <Tooltip :text="formatTaskDue(task, 'long')">
        <span
          class="shrink-0"
          :class="isTaskOverdue(task) ? 'text-ink-red-4' : ''"
        >
          {{ formatTaskDue(task) }}
        </span>
      </Tooltip>
      <span class="shrink-0 text-ink-gray-4">&middot;</span>
      <span class="truncate">{{ task.title }}</span>
    </button>
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
import { formatTaskDue, isTaskOverdue, nextFollowUp } from '@/utils/task'
import { Popover, Tooltip, call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
})

const emit = defineEmits(['open', 'change'])

const task = computed(() => nextFollowUp(props.tasks))
const saving = ref(false)
const rescheduling = ref(false)

function markDone() {
  save(
    call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: task.value.name,
      fieldname: 'status',
      value: 'Done',
    }),
  )
}

function reschedule(dueDate) {
  save(rescheduleFollowUp(task.value, dueDate))
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
