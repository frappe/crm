<template>
  <div class="w-max mx-auto">
    <div class="text-base font-medium mb-2 text-gray-800 ml-2.5">
      {{ formattedMonth }}
    </div>
    <div class="rounded-md text-sm">
      <div class="flex items-center text-xs uppercase">
        <div
          class="flex size-7.5 items-center justify-center text-center text-gray-600"
          v-for="(d, i) in ['s', 'm', 't', 'w', 't', 'f', 's']"
          :key="i"
        >
          {{ d }}
        </div>
      </div>
      <div class="flex items-center" v-for="(week, i) in datesAsWeeks" :key="i">
        <div v-for="date in week" :key="formatDate(date)">
          <Popover v-if="isHoliday(date)">
            <template #target="{ open, close }">
              <div
                class="flex size-7 cursor-pointer text-orange-700 bg-yellow-100 items-center justify-center rounded hover:bg-yellow-100 select-none m-[1px]"
                :class="{
                  '!text-ink-gray-4 !bg-gray-100': isWeekOff(date),
                }"
                @mouseover="handleMouseEnter(formatDate(date), open)"
                @mouseleave="handleMouseLeave(formatDate(date), close)"
                @click="
                  () => {
                    if (isWeekOff(date)) return
                    close()
                    editHoliday(date)
                  }
                "
              >
                {{ date.getDate() }}
              </div>
            </template>
            <template #body-main="{ close: closePopover, open: openPopover }">
              <div
                class="p-3 flex gap-2.5 text-ink-gray-9 w-80 border border-outline-gray-2 rounded-md"
                @mouseover="handleMouseEnter(formatDate(date), openPopover)"
                @mouseleave="handleMouseLeave(formatDate(date), closePopover)"
              >
                <div class="w-[5%]">
                  <div class="size-3.5 bg-orange-500 rounded-sm mt-1" />
                </div>
                <div class="grow">
                  <div class="text-sm font-semibold">
                    {{ getHolidayDescription(date) }}
                  </div>
                  <div class="text-xs mt-1">
                    {{ date.toLocaleDateString() }}
                  </div>
                </div>
                <Popover
                  v-if="!isWeekOff(date)"
                  @close="isConfirmingDelete = false"
                >
                  <template #target="{ open, close }">
                    <Button
                      icon="more-horizontal"
                      variant="ghost"
                      @click="open"
                      @mouseleave="
                        handleMouseLeave(formatDate(date) + 'dropdown', close)
                      "
                    />
                  </template>
                  <template
                    #body-main="{ close: closeDropdown, open: openDropdown }"
                  >
                    <div
                      class="p-2 flex flex-col gap-1 w-40 text-ink-gray-9 border border-outline-gray-2 rounded-md"
                      @mouseover="
                        () => {
                          handleMouseEnter(formatDate(date), openPopover)
                          handleMouseEnter(
                            formatDate(date) + 'dropdown',
                            openDropdown,
                          )
                        }
                      "
                      @mouseleave="
                        () => {
                          handleMouseLeave(formatDate(date), closePopover)
                          handleMouseLeave(
                            formatDate(date) + 'dropdown',
                            closeDropdown,
                          )
                        }
                      "
                    >
                      <Button
                        class="w-full flex !justify-start"
                        icon-left="edit"
                        variant="ghost"
                        label="Edit"
                        @click="
                          () => {
                            closePopover()
                            closeDropdown()
                            editHoliday(date)
                          }
                        "
                      />
                      <Button
                        class="w-full flex !justify-start"
                        icon-left="trash-2"
                        variant="ghost"
                        :label="
                          isConfirmingDelete
                            ? __('Confirm Delete')
                            : __('Delete')
                        "
                        :theme="isConfirmingDelete ? 'red' : 'gray'"
                        @click="
                          (e) => {
                            deleteHoliday(e, date, () => {
                              closePopover()
                              closeDropdown()
                            })
                          }
                        "
                      />
                    </div>
                  </template>
                </Popover>
              </div>
            </template>
          </Popover>
          <div
            v-else
            class="flex size-7 items-center justify-center rounded m-[1px] select-none"
            :class="{
              'cursor-pointer hover:bg-surface-gray-2': isDateInRange(date),
              'text-ink-gray-3':
                // @ts-ignore
                date.getMonth() !== currentMonth - 1 || !isDateInRange(date),
              'bg-black text-ink-white hover:!bg-black/80 hover:text-ink-white':
                formatDate(date) === dateValue && isDateInRange(date),
              'opacity-50 cursor-not-allowed': !isDateInRange(date),
            }"
            @click="isDateInRange(date) ? addHoliday(date) : null"
          >
            {{ date.getDate() }}
          </div>
        </div>
      </div>
    </div>
  </div>
  <AddHolidayModal v-model="dialog" />
</template>

<script setup>
import dayjs from 'dayjs'
import { Popover, useDatePicker } from 'frappe-ui'
import { ref, watch } from 'vue'
import { formatDate, htmlToText } from '../../../utils'
import { holidayListData } from './utils'

const dialog = ref({
  show: false,
  date: null,
  description: '',
  editing: null,
})

const {
  currentYear,
  currentMonth,
  today,
  datesAsWeeks: daw,
  formattedMonth,
} = useDatePicker()
// Workaround to fix type errors
const datesAsWeeks = daw
const isConfirmingDelete = ref(false)
const popoverTimeouts = ref({})

const props = defineProps({
  year: {
    type: Number,
    required: true,
  },
  month: {
    type: Number,
    required: true,
  },
  holidays: {
    type: Array,
    required: true,
  },
})

const dateValue = ref(formatDate(today.value))

const handleMouseEnter = (date, callback) => {
  if (popoverTimeouts.value[date]) {
    clearTimeout(popoverTimeouts.value[date])
  }
  popoverTimeouts.value[date] = setTimeout(() => {
    callback()
  }, 350)
}

const handleMouseLeave = (date, callback) => {
  if (popoverTimeouts.value[date]) {
    clearTimeout(popoverTimeouts.value[date])
  }
  popoverTimeouts.value[date] = setTimeout(() => {
    callback()
  }, 350)
}

const addHoliday = (date) => {
  dialog.value = {
    date: date,
    description: '',
    show: true,
    editing: null,
  }
}

const isDateInRange = (date) => {
  if (!holidayListData.value.from_date || !holidayListData.value.to_date)
    return false

  const checkDate = dayjs(date).startOf('day')
  const from = dayjs(holidayListData.value.from_date).startOf('day')
  const to = dayjs(holidayListData.value.to_date).endOf('day')

  return (
    (checkDate.isAfter(from) || checkDate.isSame(from, 'day')) &&
    (checkDate.isBefore(to) || checkDate.isSame(to, 'day'))
  )
}

const isHoliday = (date) => {
  if (!props.holidays?.length) return false
  const inputDate = dayjs(date).startOf('day')

  return props.holidays.some((holiday) => {
    const holidayDate = dayjs(holiday.date).startOf('day')
    return holidayDate.isSame(inputDate)
  })
}

const isWeekOff = (date) => {
  if (!props.holidays?.length) return false

  const inputDate = dayjs(date).startOf('day')
  return props.holidays.some((holiday) => {
    const holidayDate = dayjs(holiday.date).startOf('day')
    return holidayDate.isSame(inputDate) && holiday.weekly_off == 1
  })
}

const editHoliday = (date) => {
  const holiday = props.holidays.find((h) => {
    const holidayDate = formatDate(h.date)
    const editDate = formatDate(date)
    return holidayDate === editDate
  })
  dialog.value = {
    show: true,
    date: holiday.date,
    description: holiday.description,
    editing: holiday,
  }
}

const deleteHoliday = (event, date, callback) => {
  event.stopPropagation()
  event.preventDefault()
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }
  const holidayToDelete = props.holidays.find((h) => {
    const holidayDate = formatDate(h.date)
    const editDate = formatDate(date)
    return holidayDate === editDate
  })
  const index = props.holidays.findIndex((h) => {
    const holidayDate = formatDate(h.date)
    const editDate = formatDate(holidayToDelete.date)
    return holidayDate === editDate
  })

  props.holidays.splice(index, 1)
  dialog.value = {
    show: false,
    date: null,
    description: '',
    editing: null,
  }
  isConfirmingDelete.value = false
  callback()
}

const getHolidayDescription = (date) => {
  const holiday = props.holidays.find((h) => {
    const holidayDate = formatDate(h.date)
    const editDate = formatDate(date)
    return holidayDate === editDate
  })

  const text = holiday?.weekly_off
    ? `${htmlToText(holiday?.description || '')}: ${__('Recurring holiday')}`
    : htmlToText(holiday?.description || '')

  return text
}

watch(
  () => [props.year, props.month],
  ([newYear, newMonth]) => {
    currentYear.value = newYear
    currentMonth.value = newMonth
  },
  { immediate: true },
)
</script>
