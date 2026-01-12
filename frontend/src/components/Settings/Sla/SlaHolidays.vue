<template>
  <div class="flex items-center justify-between">
    <div class="flex flex-col gap-1">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __('Work schedule and holidays') }}
      </div>
      <div class="text-p-sm text-ink-gray-6 max-w-lg">
        {{
          __(
            'Set working days, hours, and holidays by selecting a predefined schedule or creating a new one',
          )
        }}
      </div>
    </div>
    <NestedPopover>
      <template #target="{ open }">
        <Button
          class="text-sm"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
          :label="slaData.holiday_list || __('Select holiday list')"
        />
      </template>
      <template #body>
        <div
          class="my-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
        >
          <div class="max-h-52 overflow-y-auto p-1">
            <div
              v-for="holiday in holidayListData.data"
              :key="holiday.name"
              class="flex items-center justify-between gap-4 rounded px-2 py-1.5 text-base text-ink-gray-8 cursor-pointer hover:bg-surface-gray-3"
              @click="
                slaData.holiday_list =
                  slaData.holiday_list === holiday.name ? '' : holiday.name
              "
            >
              <div class="flex items-center gap-2 w-full">
                <input
                  name="holiday_list"
                  :checked="holiday.name === slaData.holiday_list"
                  type="radio"
                />
                <div class="select-none">{{ holiday.name }}</div>
              </div>
              <div class="flex cursor-pointer items-center gap-1">
                <Button
                  variant="ghost"
                  @click.stop="editHolidayList(holiday)"
                  icon="edit"
                />
              </div>
            </div>
            <div
              v-if="holidayListData?.data?.length === 0"
              class="text-sm text-ink-gray-5 p-2.5 text-center"
            >
              {{ __('No holiday list found') }}
            </div>
          </div>
          <div
            class="flex flex-col gap-1 border-t border-outline-gray-modals pt-1.5 p-1"
          >
            <Button
              class="w-full !justify-start !text-ink-gray-5"
              variant="ghost"
              :label="__('Create new holiday list')"
              @click="createNewHolidayList()"
              icon-left="plus"
            />
          </div>
        </div>
      </template>
    </NestedPopover>
  </div>
  <div class="mt-5">
    <div class="rounded-md border px-2 border-outline-gray-2 text-sm">
      <div
        class="grid p-3 px-4 items-center"
        :style="{
          gridTemplateColumns: getGridTemplateColumnsForTable(columns),
        }"
        v-if="slaData.working_hours?.length !== 0"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
          :class="{
            'ml-2': column.key === 'workday',
          }"
        >
          {{ column.label }}
          <span v-if="column.isRequired" class="text-red-500">*</span>
        </div>
      </div>
      <hr
        v-if="slaData.working_hours?.length !== 0"
        class="border-outline-gray-2"
      />
      <div
        v-for="(row, index) in slaData.working_hours"
        :key="index + row.workday + row.id"
        :row="row"
      >
        <div
          class="grid gap-2 py-3.5 px-4 items-center"
          :style="{
            gridTemplateColumns: getGridTemplateColumnsForTable(columns),
          }"
        >
          <div
            v-for="column in columns"
            :key="column.key"
            class="w-full overflow-hidden whitespace-nowrap text-ellipsis"
          >
            <div
              v-if="column.key === 'start_time' || column.key === 'end_time'"
            >
              {{ formatTime(row[column.key]) }}
            </div>
            <div v-else class="ml-2">
              <select
                class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 pl-2 pr-5 bg-transparent -ml-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
                v-model="row[column.key]"
              >
                <option
                  v-for="option in workDayOptions"
                  :key="option.value"
                  :value="option.value"
                  class="text-ink-gray-8"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="flex justify-end">
            <Dropdown placement="right" :options="dropdownOptions(row)">
              <Button
                icon="more-horizontal"
                variant="ghost"
                @click="isConfirmingDelete = false"
              />
            </Dropdown>
          </div>
        </div>
        <hr
          v-if="!(index === slaData.working_hours?.length - 1)"
          class="border-outline-gray-2"
        />
      </div>
      <div
        v-if="slaData.working_hours?.length === 0"
        class="text-center p-4 text-gray-600"
      >
        {{ __('No workdays in the list') }}
      </div>
    </div>
    <div class="flex items-center justify-between mt-2.5">
      <Button
        v-if="slaData.working_hours?.length < 7"
        variant="subtle"
        :label="__('Add row')"
        @click="addWorkDay"
        icon-left="plus"
      />
      <ErrorMessage :message="slaDataErrors.working_hours" />
    </div>
  </div>
  <WorkDayModal v-model="dialog" :workDaysList="slaData.working_hours" />
</template>

<script setup>
import {
  Button,
  createListResource,
  Dropdown,
  ErrorMessage,
  NestedPopover,
} from 'frappe-ui'
import { ConfirmDelete, getGridTemplateColumnsForTable } from '../../../utils'
import { slaData, slaDataErrors } from './utils'
import { ref } from 'vue'
import WorkDayModal from './WorkDayModal.vue'

const dialog = ref({
  show: false,
  isEditing: false,
  data: {},
})

const isConfirmingDelete = ref(false)

const holidayListData = createListResource({
  doctype: 'CRM Holiday List',
  fields: ['name'],
  auto: true,
})

const dropdownOptions = (workDay) => [
  {
    label: __('Edit'),
    onClick: () => editWorkDay(workDay),
    icon: 'edit',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteWorkDay(workDay),
    isConfirmingDelete,
  }),
]

const columns = [
  {
    label: __('Day'),
    key: 'workday',
    isRequired: true,
  },
  {
    label: __('Start time'),
    key: 'start_time',
    isRequired: true,
  },
  {
    label: __('End time'),
    key: 'end_time',
    isRequired: true,
  },
]

const workDayOptions = [
  { label: 'Monday', value: 'Monday' },
  { label: 'Tuesday', value: 'Tuesday' },
  { label: 'Wednesday', value: 'Wednesday' },
  { label: 'Thursday', value: 'Thursday' },
  { label: 'Friday', value: 'Friday' },
  { label: 'Saturday', value: 'Saturday' },
  { label: 'Sunday', value: 'Sunday' },
]

const createNewHolidayList = () => {
  window.open(`${window.location.origin}/app/crm-holiday-list`)
}

const deleteWorkDay = (workDay) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  const item = slaData.value.working_hours.indexOf(workDay)
  if (item !== -1) {
    slaData.value.working_hours.splice(item, 1)
  }
}

const editWorkDay = (workDay) => {
  dialog.value.show = true
  dialog.value.isEditing = true
  dialog.value.data = {
    workday: workDay.workday,
    start_time: workDay.start_time,
    end_time: workDay.end_time,
  }
}

const addWorkDay = () => {
  const usedDays = new Set(
    slaData.value.working_hours.map((day) => day.workday),
  )
  const nextDay =
    workDayOptions.find((day) => !usedDays.has(day.label))?.label ||
    workDayOptions[0].label

  slaData.value.working_hours.push({
    workday: nextDay,
    start_time: '09:00:00',
    end_time: '17:00:00',
    id: Math.random().toString(36).substring(2, 9),
  })
}

const editHolidayList = (holidayList) => {
  window.open(
    `${window.location.origin}/app/crm-holiday-list/${holidayList.name}`,
  )
}

const formatTime = (time) => {
  if (!time) return '00:00'
  const [hours, minutes] = time.split(':')
  const date = new Date()
  date.setHours(parseInt(hours) || 0, parseInt(minutes) || 0, 0)

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}
</script>

<style scoped>
input[type='radio'] {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  border: 2px solid #c5c2c2;
  border-radius: 50%;
  outline: none;
  transition: all 0.2s ease;
  background-color: white;
}

input[type='radio']:checked {
  background-color: black;
  border: 2px solid #000;
}

input[type='radio']:checked::after {
  content: '';
  background-color: #fff;
}

input[type='radio']:focus {
  outline: none !important;
  box-shadow: none !important;
}

[data-theme='dark'] input[type='radio'] {
  border: 2px solid #525252;
  background-color: transparent;
}

[data-theme='dark'] input[type='radio']:checked {
  background-color: #171717;
  border: 2px solid #fff;
}

[data-theme='dark'] input[type='radio']:checked::after {
  background-color: #171717;
}
</style>
