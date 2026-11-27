import { dayjs } from 'frappe-ui'
import { ref } from 'vue'
import { activeSettingsPage } from '@/composables/settings'
import { getFormat } from '@/utils'
import { buildHolidays } from './utils'
import type { Holiday, HolidayErrors, HolidayListForm } from './types'

export const holidayScreen = ref<{
  screen: 'list' | 'view'
  // null for a list that is not saved yet.
  name: string | null
  // The SLA policy the list was opened from, so Back can return to it.
  returnToSla?: string | null
}>({ screen: 'list', name: null })

function emptyForm(): HolidayListForm {
  return {
    name: '',
    holiday_list_name: '',
    description: '',
    from_date: '',
    to_date: '',
    holidays: [],
    recurring_holidays: [],
  }
}

function emptyErrors(): HolidayErrors {
  return { holiday_list_name: '', from_date: '', to_date: '', holidays: '' }
}

export const holidayData = ref<HolidayListForm>(emptyForm())
export const holidayDataErrors = ref<HolidayErrors>(emptyErrors())

export function resetHolidayData() {
  holidayData.value = emptyForm()
}

export function resetHolidayDataErrors() {
  holidayDataErrors.value = emptyErrors()
}

export function validateHoliday(key?: keyof HolidayErrors): HolidayErrors {
  const { holiday_list_name, from_date, to_date, holidays } = holidayData.value
  const errors = holidayDataErrors.value
  const check = (field: keyof HolidayErrors) => !key || key === field

  if (check('holiday_list_name')) {
    errors.holiday_list_name = holiday_list_name.trim()
      ? ''
      : __('Holiday list name is required')
  }
  if (check('from_date')) {
    errors.from_date = from_date ? '' : __('From date is required')
  }
  if (check('to_date')) {
    errors.to_date = to_date ? '' : __('To date is required')
  }
  if (to_date && (check('from_date') || check('to_date'))) {
    errors.to_date =
      from_date > to_date ? __('To date cannot be before from date') : ''
  }
  if (check('holidays')) {
    const outside = holidays.find(
      (holiday) =>
        !holiday.weekly_off &&
        (holiday.date < from_date || holiday.date > to_date),
    )
    errors.holidays = outside
      ? __('{0} on {1} is outside the date range', [
          outside.description,
          formatHolidayDate(outside.date),
        ])
      : ''
  }
  return errors
}

// In the site's date format; dates are YYYY-MM-DD so no timezone shift applies.
export function formatHolidayDate(date: string): string {
  return date ? dayjs(date).format(getFormat('', '', true, false, false)) : ''
}

export function updateWeeklyOffDates() {
  const { holidays, recurring_holidays, from_date, to_date } = holidayData.value
  holidayData.value.holidays = buildHolidays(
    holidays,
    recurring_holidays,
    from_date,
    to_date,
  )
  if (holidayDataErrors.value.holidays) validateHoliday('holidays')
}

// Adds a single holiday, or replaces the one being edited; returns an error, empty on success.
export function saveHoliday(
  date: string,
  description: string,
  editing: Holiday | null,
): string {
  const { holidays, from_date, to_date } = holidayData.value
  if (date < from_date || date > to_date) {
    return __('Choose a date between {0} and {1}', [
      formatHolidayDate(from_date),
      formatHolidayDate(to_date),
    ])
  }
  const clash = holidays.some(
    (holiday) =>
      holiday.date === date && !holiday.weekly_off && holiday !== editing,
  )
  if (clash) {
    return __('{0} is already a holiday', [formatHolidayDate(date)])
  }

  // A single holiday takes the place of a weekly off on the same date.
  const others = holidays.filter(
    (holiday) =>
      holiday !== editing && !(holiday.weekly_off && holiday.date === date),
  )
  holidayData.value.holidays = [
    ...others,
    { date, description: description.trim(), weekly_off: 0 },
  ]
  updateWeeklyOffDates()
  return ''
}

export function removeHoliday(holiday: Holiday) {
  holidayData.value.holidays = holidayData.value.holidays.filter(
    (row) => row !== holiday,
  )
  // Brings back a weekly off the holiday was covering.
  updateWeeklyOffDates()
}

// Opens the Business Holidays tab on a list, or on a new one when name is null.
export function openHolidayList(
  name: string | null,
  returnToSla: string | null = null,
) {
  if (!name) resetHolidayData()
  holidayScreen.value = { screen: 'view', name, returnToSla }
  activeSettingsPage.value = __('Business Holidays')
}
