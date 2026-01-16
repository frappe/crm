<template>
  <div class="rounded-md border px-2 border-outline-gray-2 text-sm">
    <div
      class="grid p-3 px-4 items-center gap-2"
      :style="{
        gridTemplateColumns: '1fr 4fr 22px',
      }"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
      </div>
    </div>
    <hr class="border-outline-gray-2" />
    <div v-for="(holiday, index) in holidays" :key="holiday.name">
      <div
        class="grid gap-2 py-3.5 px-4 items-center"
        :style="{ gridTemplateColumns: '1fr 4fr 22px' }"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="w-full overflow-hidden whitespace-nowrap text-ellipsis"
        >
          <input
            v-if="column.key === 'description'"
            :type="'text'"
            :placeholder="__('Description')"
            v-model="holiday[column.key]"
            class="bg-white dark:bg-surface-gray-1 w-full text-base px-0 focus:!ring-0 border-none dark:hover:bg-surface-gray-1 outline-none no-underline focus:!outline-none"
          />
          <div v-else>
            {{ dayjs(holiday[column.key]).format('DD MMM YYYY') }}
          </div>
        </div>
        <div class="flex justify-end">
          <Dropdown placement="right" :options="dropdownOptions(holiday)">
            <Button
              icon="more-horizontal"
              variant="ghost"
              @click="isConfirmingDelete = false"
            />
          </Dropdown>
        </div>
      </div>
      <hr class="border-outline-gray-2" v-if="index !== holidays.length - 1" />
    </div>
    <div v-if="holidays?.length === 0" class="text-center p-4 text-gray-600">
      {{ __('No items in the list') }}
    </div>
  </div>
  <AddHolidayModal v-model="dialog" />
</template>

<script setup>
import { computed, ref } from 'vue'
import dayjs from 'dayjs'
import { Dropdown } from 'frappe-ui'
import { ConfirmDelete, formatDate } from '../../../utils'
import { holidayListData } from './utils'

const isConfirmingDelete = ref(false)

const dropdownOptions = (holiday) => [
  {
    label: __('Edit'),
    onClick: () => editHoliday(holiday),
    icon: 'edit',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteHoliday(holiday),
    isConfirmingDelete,
  }),
]

const dialog = ref({
  show: false,
  date: null,
  description: '',
  editing: null,
})

const holidays = computed(() => {
  return holidayListData.value.holidays.filter((item) => {
    return item.weekly_off == 0
  })
})

const columns = [
  {
    label: __('Date'),
    key: 'date',
  },
  {
    label: __('Description'),
    key: 'description',
  },
]

const editHoliday = (holiday) => {
  dialog.value = {
    show: true,
    date: holiday.date,
    description: holiday.description,
    editing: holiday,
  }
}

const deleteHoliday = (holidayToDelete) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }
  const index = holidayListData.value.holidays.findIndex((h) => {
    const holidayDate = formatDate(h.date)
    const editDate = formatDate(holidayToDelete?.date)
    return holidayDate === editDate
  })

  holidayListData.value.holidays.splice(index, 1)
  isConfirmingDelete.value = false
}
</script>
