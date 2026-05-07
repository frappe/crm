<template>
  <Dialog
    v-model="dialog.show"
    :options="{
      size: 'sm',
      title: dialog.editing ? __('Edit Holiday') : __('Add Holiday'),
    }"
    @after-leave="resetForm"
  >
    <template #body-content>
      <div class="flex flex-col gap-4 mt-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Date')" required />
          <DatePicker
            :value="dayjs(dialog.date).format('MM-DD-YYYY')"
            @update:model-value="dialog.date = $event"
            :format="getFormat()"
            variant="subtle"
            :placeholder="__('Date')"
            class="w-full"
            id="date"
            required
            @change="errors.date = ''"
          />
          <ErrorMessage :message="errors.date" />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormControl
            :type="'textarea'"
            size="sm"
            variant="subtle"
            :placeholder="__('National holiday, etc.')"
            :label="__('Description')"
            v-model="dialog.description"
            required
            @change="errors.description = ''"
          />
          <ErrorMessage :message="errors.description" />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="subtle"
          theme="gray"
          :label="__('Cancel')"
          @click="dialog.show = false"
        />
        <Button
          variant="solid"
          icon-left="plus"
          :label="__('Add Holiday')"
          @click="onSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  FormControl,
  Button,
  FormLabel,
  toast,
  ErrorMessage,
  DatePicker,
} from 'frappe-ui'
import { ref } from 'vue'
import dayjs from 'dayjs'
import { formatDate, getFormat } from '../../../utils'
import { holidayListData } from './utils'

const dialog = defineModel()

const errors = ref({
  date: '',
  description: '',
})

const resetForm = () => {
  dialog.value.date = new Date()
  dialog.value.description = ''
  errors.value = {
    date: '',
    description: '',
  }
}

const onSave = () => {
  if (dialog.value.description?.trim() === '') {
    errors.value.description = __('Please enter a description')
  }
  if (!dialog.value.date) {
    errors.value.date = __('Please enter a valid date')
  }

  if (errors.value.date || errors.value.description) {
    return
  }

  const holidayDate = dayjs(dialog.value.date).startOf('day')
  const fromDate = dayjs(holidayListData.value.from_date).startOf('day')
  const toDate = dayjs(holidayListData.value.to_date).startOf('day')

  if (holidayDate.isBefore(fromDate) || holidayDate.isAfter(toDate)) {
    toast.error(
      __(`Holiday date must be between {0} and {1}`, [
        formatDate(holidayListData.value.from_date),
        formatDate(holidayListData.value.to_date),
      ]),
    )
    return
  }

  if (dialog.value.editing) {
    const holidayExists = holidayListData.value.holidays.find(
      (h) => formatDate(h.date) === formatDate(dialog.value.date),
    )

    // If the holiday exists and user is trying to add a new holiday on the same date, show error
    if (
      holidayExists &&
      formatDate(holidayExists.date) !== formatDate(dialog.value.editing.date)
    ) {
      toast.error(__('Holiday already exists'))
      return
    }
    const holidayIndex = holidayListData.value.holidays.indexOf(
      dialog.value.editing,
    )
    holidayListData.value.holidays.splice(holidayIndex, 1, {
      ...dialog.value,
      weekly_off: 0,
    })
  } else {
    const index = holidayListData.value.holidays.findIndex(
      (h) => formatDate(h.date) === formatDate(dialog.value.date),
    )
    if (index !== -1) {
      toast.error(__('Holiday already exists'))
      return
    }
    holidayListData.value.holidays.push({
      ...dialog.value,
      weekly_off: 0,
    })
  }

  dialog.value = {
    show: false,
    date: null,
    description: '',
    editing: null,
  }
}
</script>
