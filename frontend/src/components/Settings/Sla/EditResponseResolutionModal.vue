<template>
  <Dialog
    v-model="dialog"
    :options="{
      title: __('Edit Response & Resolution'),
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="priorityData.priority"
          type="select"
          size="sm"
          variant="subtle"
          :placeholder="__('Select Priority')"
          :label="__('Priority')"
          :options="priorityOptions"
          required
          class="text-ink-gray-8"
        />
        <div>
          <FormLabel :label="__('First Response Time')" required />
          <DurationInput
            class="mt-2 w-full"
            :value="priorityData.first_response_time"
            :long-form="true"
            size="sm"
            variant="subtle"
            @change="(v) => (priorityData.first_response_time = v)"
          />
        </div>
        <Checkbox
          v-model="priorityData.default_priority"
          :label="__('Set Default Priority')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button
            variant="subtle"
            :theme="isConfirmingDelete ? 'red' : 'gray'"
            :label="isConfirmingDelete ? __('Confirm Delete') : __('Delete')"
            icon-left="trash-2"
            @click="deleteItem"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            :label="__('Cancel')"
            @click="dialog = false"
          />
          <Button variant="solid" :label="__('Save')" @click="onSave" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  Checkbox,
  Dialog,
  FormControl,
  FormLabel,
  toast,
} from 'frappe-ui'
import { inject, ref, watch } from 'vue'
import { slaData } from './utils'
import DurationInput from '../../Controls/DurationInput.vue'

const dialog = defineModel({ type: Boolean })
const isConfirmingDelete = ref(false)

const props = defineProps({
  priority: { type: Object, required: true },
})

const priorityOptions = inject('priorityOptions')

const priorityData = ref({
  priority: props.priority.priority,
  first_response_time: props.priority.first_response_time,
  default_priority: props.priority.default_priority,
})

const validateForm = () => {
  if (!priorityData.value.priority) {
    toast.error(__('Please select a Priority'))
    return false
  }

  const responseTime = parseInt(priorityData.value.first_response_time)
  if (isNaN(responseTime) || responseTime <= 0) {
    toast.error(__('Response Time is required'))
    return false
  }

  if (priorityData.value.default_priority) {
    slaData.value.priorities.forEach((priority) => {
      priority.default_priority = false
    })
  }

  return true
}

const deleteItem = (event) => {
  event.preventDefault()
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  slaData.value.priorities.splice(
    slaData.value.priorities.indexOf(props.priority),
    1,
  )
  dialog.value = false
}

const onSave = () => {
  if (!validateForm()) return
  const index = slaData.value.priorities.findIndex(
    (p) => p.priority === props.priority.priority,
  )
  const priority = slaData.value.priorities[index]
  if (index !== -1) {
    priority.priority = priorityData.value.priority
    priority.first_response_time = priorityData.value.first_response_time
    priority.default_priority = priorityData.value.default_priority
  }

  dialog.value = false
}

watch(dialog, (newValue) => {
  if (newValue) {
    priorityData.value = {
      priority: props.priority.priority,
      first_response_time: props.priority.first_response_time,
      default_priority: props.priority.default_priority,
    }
  }
})
</script>
