<template>
  <Popover v-model:open="open" side="bottom" align="start">
    <template #trigger>
      <div class="flex">
        <slot>
          <Button :tooltip="__('Follow up')" icon="lucide-calendar-clock" />
        </slot>
      </div>
    </template>
    <template #default>
      <div class="flex w-64 flex-col gap-1.5 p-1.5">
        <TextInput
          v-model="note"
          size="sm"
          :placeholder="title"
          :disabled="creating"
        />
        <FollowUpDates :disabled="creating" @select="create" />
        <div class="border-t border-outline-elevation-2 pt-1.5">
          <ItemListRow
            role="button"
            tabindex="0"
            class="cursor-pointer outline-none hover:bg-surface-gray-3 focus-visible:bg-surface-gray-3"
            @click="openFullForm"
            @keydown.enter.space.prevent="openFullForm"
          >
            {{ __('More options') }}
          </ItemListRow>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import FollowUpDates from '@/components/FollowUp/FollowUpDates.vue'
import { createFollowUp, openFollowUpForm } from '@/composables/followUp'
import { useCrmOnboarding } from '@/composables/onboarding'
import { useTelemetry } from '@framework/ui/telemetry'
import { ItemListRow, Popover, TextInput, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  title: { type: String, required: true },
})

const emit = defineEmits(['created'])

const { completeStep } = useCrmOnboarding()
const { capture } = useTelemetry()

const open = ref(false)
const note = ref('')
const creating = ref(false)

async function create(dueDate) {
  creating.value = true
  try {
    const task = await createFollowUp({ ...taskFields(), dueDate })
    toast.success(__('Follow-up added'))
    open.value = false
    note.value = ''
    afterCreate(task)
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not add the follow-up'))
  } finally {
    creating.value = false
  }
}

function openFullForm() {
  open.value = false
  openFollowUpForm({ ...taskFields(), afterInsert: afterCreate })
  note.value = ''
}

function afterCreate(task) {
  completeStep('create_first_task')
  capture('follow_up_created', { doctype: props.doctype })
  emit('created', task)
}

function taskFields() {
  return {
    doctype: props.doctype,
    docname: props.docname,
    title: note.value.trim() || props.title,
  }
}
</script>
