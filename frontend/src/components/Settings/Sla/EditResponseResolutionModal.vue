<template>
  <Dialog
    v-model="dialog"
    :options="{
      title: __('Edit response and resolution'),
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="select"
          size="sm"
          variant="subtle"
          :placeholder="__('Select Priority')"
          :label="__('Priority')"
          v-model="priorityData.priority"
          :options="priorityOptions"
          required
          class="text-ink-gray-8"
        />
        <div>
          <FormLabel :label="__('First response time')" required />
          <Popover class="mt-2">
            <template #target="{ togglePopover }" class="w-max">
              <div
                @click="togglePopover()"
                class="w-full bg-surface-gray-2 rounded p-1.5 px-2 text-base text-ink-gray-8 cursor-pointer hover:bg-surface-gray-3"
              >
                <div v-if="priorityData.first_response_time">
                  {{ formatTimeHMS(priorityData.first_response_time) }}
                </div>
                <div v-else class="text-gray-500">{{ __('Select time') }}</div>
              </div>
            </template>
            <template #body>
              <div class="absolute bg-surface-white top-2 rounded">
                <DurationPicker
                  v-model="priorityData.first_response_time"
                  :options="{ seconds: false }"
                />
              </div>
            </template>
          </Popover>
        </div>
        <Checkbox
          v-model="priorityData.default_priority"
          :label="__('Set default priority')"
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
            @click="deleteItem"
            icon-left="trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog = false"
            :label="__('Cancel')"
          />
          <Button variant="solid" @click="onSave" :label="__('Save')" />
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
  Popover,
  toast,
} from 'frappe-ui'
import { inject, ref, watch } from 'vue'
import { slaData } from './utils'
import { formatTimeHMS } from '../../../utils'
import DurationPicker from '../../Controls/DurationPicker.vue'

const dialog = defineModel()
const isConfirmingDelete = ref(false)

const props = defineProps({
  priority: {
    type: Object,
    required: true,
  },
})

const priorityOptions = inject('priorityOptions')

const priorityData = ref({
  priority: props.priority.priority,
  first_response_time: props.priority.first_response_time,
  default_priority: props.priority.default_priority,
})

const validateForm = () => {
  if (!priorityData.value.priority) {
    toast.error(__('Please select a priority'))
    return false
  }

  const responseTime = parseInt(priorityData.value.first_response_time)
  if (isNaN(responseTime) || responseTime <= 0) {
    toast.error(__('Response time is required'))
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
