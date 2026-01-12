<template>
  <Dialog
    v-model="dialog.show"
    @after-leave="resetForm"
    :options="{ title: __('Edit workday') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            type="select"
            size="sm"
            variant="subtle"
            :placeholder="__('Select Workday')"
            :label="__('Workday')"
            v-model="workDayData.workday"
            :options="workdayOptions"
            class="text-ink-gray-8"
            :class="{ 'border-red-500': errors.workday }"
            @blur="validateField('workday')"
          />
          <ErrorMessage :message="errors.workday" class="mt-2" />
        </div>

        <div>
          <FormControl
            type="time"
            size="sm"
            variant="subtle"
            :placeholder="__('Start Time')"
            :label="__('Start Time')"
            v-model="workDayData.start_time"
            :class="{ 'border-red-500': errors.start_time }"
            @blur="validateField('start_time')"
          />
          <ErrorMessage :message="errors.start_time" class="mt-2" />
        </div>

        <div>
          <FormControl
            type="time"
            size="sm"
            variant="subtle"
            :placeholder="__('End Time')"
            :label="__('End Time')"
            v-model="workDayData.end_time"
            :class="{ 'border-red-500': errors.end_time }"
            @blur="validateTimeRange"
          />
          <ErrorMessage :message="errors.end_time" class="mt-2" />
        </div>
      </div>
    </template>
    <template #actions>
      <div
        class="flex"
        :class="{
          'justify-between': dialog.isEditing,
          'justify-end': !dialog.isEditing,
        }"
      >
        <div v-if="dialog.isEditing">
          <Button
            variant="subtle"
            :theme="isConfirmingDelete ? 'red' : 'gray'"
            :label="isConfirmingDelete ? __('Confirm Delete') : __('Delete')"
            @click="deleteWorkDay"
            icon-left="trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog.show = false"
            :label="__('Cancel')"
          />
          <Button variant="solid" @click="onSave" :label="__('Save')" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { Dialog, FormControl, Button, toast } from 'frappe-ui'

const ALL_WORKDAY_OPTIONS = [
  { label: 'Monday', value: 'Monday' },
  { label: 'Tuesday', value: 'Tuesday' },
  { label: 'Wednesday', value: 'Wednesday' },
  { label: 'Thursday', value: 'Thursday' },
  { label: 'Friday', value: 'Friday' },
  { label: 'Saturday', value: 'Saturday' },
  { label: 'Sunday', value: 'Sunday' },
]

const props = defineProps({
  workDaysList: {
    type: Array,
    required: true,
  },
})

const isConfirmingDelete = ref(false)

const dialog = defineModel({
  required: true,
  default: () => ({
    show: false,
    isEditing: false,
    data: {
      workday: '',
      start_time: '',
      end_time: '',
    },
  }),
})

const workDayData = reactive({
  workday: '',
  start_time: '',
  end_time: '',
})

const errors = reactive({
  workday: '',
  start_time: '',
  end_time: '',
})

const originalWorkday = computed(() => dialog.value.data?.workday || '')

const workdayOptions = computed(() => {
  const existingDays = props.workDaysList.map((item) => item.workday)
  return ALL_WORKDAY_OPTIONS.filter((option) => {
    return (
      !existingDays.includes(option.value) ||
      (dialog.value.isEditing && option.value === originalWorkday.value)
    )
  })
})

// Helper functions
function formatTimeToHHMMSS(timeStr) {
  if (!timeStr) return ''

  const timeMatch = timeStr.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/)
  if (!timeMatch) return ''

  const [, hours, minutes, seconds = '00'] = timeMatch
  return `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}:${seconds.padStart(2, '0')}`
}

function resetErrors() {
  errors.workday = ''
  errors.start_time = ''
  errors.end_time = ''
}

function resetForm() {
  workDayData.workday = ''
  workDayData.start_time = ''
  workDayData.end_time = ''
  resetErrors()
  isConfirmingDelete.value = false
}

function findWorkdayIndex(workday) {
  return props.workDaysList.findIndex((item) => item.workday === workday)
}

// Validation
function validateField(field) {
  if (!workDayData[field]) {
    errors[field] = __('This field is required')
    return false
  }
  errors[field] = ''
  return true
}

function validateTimeRange() {
  if (!workDayData.start_time) {
    errors.start_time = __('Start time is required')
  }
  if (!workDayData.end_time) {
    errors.end_time = __('End time is required')
  }
  if (!workDayData.start_time || !workDayData.end_time) {
    return false
  }

  const [startHours, startMinutes] = workDayData.start_time
    .split(':')
    .map(Number)
  const [endHours, endMinutes] = workDayData.end_time.split(':').map(Number)

  const startTotalMinutes = startHours * 60 + startMinutes
  const endTotalMinutes = endHours * 60 + endMinutes

  if (endTotalMinutes <= startTotalMinutes) {
    errors.end_time = __('End time must be after start time')
    return false
  }

  errors.end_time = ''
  return true
}

function validateForm() {
  const isWorkdayValid = validateField('workday')
  const isStartTimeValid = validateField('start_time')
  const isEndTimeValid = validateField('end_time') && validateTimeRange()

  return isWorkdayValid && isStartTimeValid && isEndTimeValid
}

// Actions
function deleteWorkDay(event) {
  event.preventDefault()

  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  const itemIndex = findWorkdayIndex(originalWorkday.value)
  if (itemIndex !== -1) {
    props.workDaysList.splice(itemIndex, 1)
  }

  dialog.value.show = false
}

function onSave() {
  if (!validateForm()) {
    toast.error(__('Please fix the errors in the form'))
    return
  }

  try {
    const formattedData = {
      workday: workDayData.workday,
      start_time: formatTimeToHHMMSS(workDayData.start_time),
      end_time: formatTimeToHHMMSS(workDayData.end_time),
    }

    if (dialog.value.isEditing) {
      const itemIndex = findWorkdayIndex(originalWorkday.value)
      if (itemIndex !== -1) {
        const updatedItem = {
          ...props.workDaysList[itemIndex],
          ...formattedData,
        }
        props.workDaysList.splice(itemIndex, 1, updatedItem)
      }
    } else {
      props.workDaysList.push(formattedData)
    }

    dialog.value.show = false
  } catch (error) {
    toast.error(__('Failed to save workday: {0}', [error.message || error]))
  }
}

watch(
  () => dialog.value.show,
  (isOpen) => {
    if (isOpen) {
      if (dialog.value.isEditing && dialog.value.data) {
        workDayData.workday = dialog.value.data.workday
        workDayData.start_time = formatTimeToHHMMSS(
          dialog.value.data.start_time,
        )
        workDayData.end_time = formatTimeToHHMMSS(dialog.value.data.end_time)
      } else {
        resetForm()
      }
    }
  },
)
</script>
