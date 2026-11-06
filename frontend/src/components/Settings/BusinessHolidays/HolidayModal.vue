<template>
  <Dialog
    v-model:open="modal.show"
    size="sm"
    :title="modal.editing ? __('Edit Holiday') : __('Add Holiday')"
    @after-leave="errors = { date: '', description: '' }"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <DatePicker
            v-model="modal.date"
            :label="__('Date')"
            required
            variant="subtle"
            :placeholder="__('Select date')"
            class="w-full"
            :format="dateFormat"
            :min="holidayData.from_date"
            :max="holidayData.to_date"
            @update:model-value="errors.date = ''"
          />
          <ErrorMessage :message="errors.date" />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormControl
            v-model="modal.description"
            type="textarea"
            size="sm"
            variant="subtle"
            :placeholder="__('National holiday, company offsite, etc.')"
            :label="__('Description')"
            required
            @update:model-value="errors.description = ''"
          />
          <ErrorMessage :message="errors.description" />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <Button
          v-if="modal.editing"
          variant="subtle"
          theme="red"
          :label="__('Delete')"
          icon-left="lucide-trash-2"
          @click="onDelete()"
        />
        <div class="flex gap-2 ml-auto">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="modal.show = false"
          />
          <Button
            variant="solid"
            :label="modal.editing ? __('Update') : __('Add')"
            @click="onSave()"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Button,
  DatePicker,
  Dialog,
  ErrorMessage,
  FormControl,
} from 'frappe-ui'
import { ref } from 'vue'
import { getFormat } from '@/utils'
import { holidayData, removeHoliday, saveHoliday } from './store'
import type { HolidayModalState } from './types'

const modal = defineModel<HolidayModalState>({ required: true })

const dateFormat = getFormat('', '', true, false, false)
const errors = ref({ date: '', description: '' })

function onSave() {
  const { date, description, editing } = modal.value
  errors.value = {
    date: date ? '' : __('Date is required'),
    description: description.trim() ? '' : __('Description is required'),
  }
  if (errors.value.date || errors.value.description) return

  errors.value.date = saveHoliday(date, description, editing)
  if (!errors.value.date) modal.value.show = false
}

function onDelete() {
  if (modal.value.editing) removeHoliday(modal.value.editing)
  modal.value.show = false
}
</script>
