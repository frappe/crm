import { dayjs } from 'frappe-ui'
import { ref } from 'vue'

export const holidayListActiveStep = ref({
  screen: 'list',
  data: null,
})

export const holidayListDataErrors = ref({
  holiday_list_name: '',
  from_date: '',
  to_date: '',
  dateRange: '',
})

export const resetHolidayListErrors = () => {
  holidayListDataErrors.value = {
    holiday_list_name: '',
    from_date: '',
    to_date: '',
    dateRange: '',
  }
}

export const holidayListData = ref({
  holiday_list_name: '',
  description: '',
  loading: false,
  total_holidays: 0,
  holidays: [],
  from_date: null,
  to_date: null,
  recurring_holidays: [],
})

export const resetHolidayListData = () => {
  holidayListData.value = {
    holiday_list_name: '',
    description: '',
    loading: false,
    total_holidays: 0,
    holidays: [],
    from_date: null,
    to_date: null,
    recurring_holidays: [],
  }
}

export const validateHolidayListData = (key) => {
  const validateField = (field) => {
    if (key && field !== key) return

    switch (field) {
      case 'holiday_list_name':
        if (!holidayListData.value.holiday_list_name?.trim()) {
          holidayListDataErrors.value.holiday_list_name =
            'Holiday list name is required'
        } else {
          holidayListDataErrors.value.holiday_list_name = ''
        }
        break
      case 'from_date':
        if (!holidayListData.value.from_date) {
          holidayListDataErrors.value.from_date = 'Start date is required'
        } else {
          holidayListDataErrors.value.from_date = ''
        }

        if (holidayListData.value.to_date) {
          const startDate = new Date(holidayListData.value.from_date)
          const endDate = new Date(holidayListData.value.to_date)

          if (startDate > endDate) {
            holidayListDataErrors.value.dateRange =
              'Start date cannot be after end date'
          } else {
            holidayListDataErrors.value.dateRange = ''
          }
        }
        break
      case 'to_date':
        if (!holidayListData.value.to_date) {
          holidayListDataErrors.value.to_date = 'End date is required'
        } else {
          holidayListDataErrors.value.to_date = ''
        }

        if (holidayListData.value.from_date) {
          const startDate = new Date(holidayListData.value.from_date)
          const endDate = new Date(holidayListData.value.to_date)

          if (startDate > endDate) {
            holidayListDataErrors.value.dateRange =
              'Start date cannot be after end date'
          } else {
            holidayListDataErrors.value.dateRange = ''
          }
        }
        break
      default:
        break
    }
  }

  if (key) {
    validateField(key)
  } else {
    Object.keys(holidayListDataErrors.value).forEach(validateField)
  }

  return holidayListDataErrors.value
}

export const getRepetitionText = (repetition) => {
  const parts = []

  if (repetition.all) {
    parts.push('week')
  } else {
    if (repetition.first) parts.push('first')
    if (repetition.second) parts.push('second')
    if (repetition.third) parts.push('third')
    if (repetition.fourth) parts.push('fourth')
    if (repetition.fifth) parts.push('fifth')

    if (parts.length === 0) return ''

    if (parts.length > 1) {
      const last = parts.pop()
      parts[parts.length - 1] = `${parts[parts.length - 1]} and ${last}`
    }

    parts[0] = parts[0].charAt(0) + parts[0].slice(1)
    return `Every ${parts.join(', ')} week`
  }

  return parts[0] ? `Every ${parts[0]}` : ''
}

export const validateHoliday = (key) => {
  const validateField = (field) => {
    if (key && field !== key) return

    switch (field) {
      case 'holiday_list_name':
        if (!holidayListData.value.holiday_list_name?.trim()) {
          holidayListDataErrors.value.holiday_list_name =
            'Holiday list name is required'
        } else {
          holidayListDataErrors.value.holiday_list_name = ''
        }
        break
      case 'from_date':
        if (!holidayListData.value.from_date) {
          holidayListDataErrors.value.from_date = 'Start date is required'
        } else {
          holidayListDataErrors.value.from_date = ''
        }

        if (holidayListData.value.to_date) {
          const startDate = new Date(holidayListData.value.from_date)
          const endDate = new Date(holidayListData.value.to_date)

          if (startDate > endDate) {
            holidayListDataErrors.value.dateRange =
              'Start date cannot be after end date'
          } else {
            holidayListDataErrors.value.dateRange = ''
          }
        }
        break
      case 'to_date':
        if (!holidayListData.value.to_date) {
          holidayListDataErrors.value.to_date = 'End date is required'
        } else {
          holidayListDataErrors.value.to_date = ''
        }

        if (holidayListData.value.from_date) {
          const startDate = new Date(holidayListData.value.from_date)
          const endDate = new Date(holidayListData.value.to_date)

          if (startDate > endDate) {
            holidayListDataErrors.value.dateRange =
              'Start date cannot be after end date'
          } else {
            holidayListDataErrors.value.dateRange = ''
          }
        }
        break
      default:
        break
    }
  }

  if (key) {
    validateField(key)
  } else {
    Object.keys(holidayListDataErrors.value).forEach(validateField)
  }

  return holidayListDataErrors.value
}

export function updateWeeklyOffDates() {
  const newHolidays = holidayListData.value.holidays.filter(
    (h) => !h.weekly_off,
  )

  for (const day of holidayListData.value.recurring_holidays) {
    const weeklyOffs = getWeeklyOffDates(
      holidayListData.value.from_date,
      holidayListData.value.to_date,
      day.day,
      newHolidays,
      day.repetition,
    )

    newHolidays.push(...weeklyOffs)
  }
  holidayListData.value.holidays = newHolidays
}

function getWeekOfMonth(date) {
  const firstDayOfMonth = date.startOf('month')
  const firstDayOfWeek = firstDayOfMonth.day()
  const offset = (date.date() + firstDayOfWeek - 1) / 7
  return Math.ceil(offset)
}

function getWeeklyOffDateList(
  startDate,
  endDate,
  weeklyOff,
  holidays = [],
  repetition,
) {
  const start = dayjs(startDate)
  const end = dayjs(endDate)
  const dateList = []

  const dayMap = {
    sunday: 0,
    monday: 1,
    tuesday: 2,
    wednesday: 3,
    thursday: 4,
    friday: 5,
    saturday: 6,
  }

  const targetDay = dayMap[weeklyOff.toLowerCase()]
  if (targetDay === undefined) {
    return dateList
  }

  const existingDates = holidays.map((h) =>
    dayjs(h.date).startOf('day').toDate(),
  )

  let currentDate = start.day(targetDay)
  if (currentDate.isBefore(start, 'day')) {
    currentDate = currentDate.add(1, 'week')
  }
  const useAllOccurrences = !repetition || repetition.all

  while (!currentDate.isAfter(end, 'day')) {
    const currentDateObj = currentDate.toDate()
    const currentDateStart = dayjs(currentDateObj).startOf('day')

    if (useAllOccurrences || shouldIncludeDate(currentDate, repetition)) {
      if (
        !existingDates.some((d) =>
          dayjs(d).startOf('day').isSame(currentDateStart),
        )
      ) {
        dateList.push(currentDateObj)
      }
    }
    currentDate = currentDate.add(1, 'week')
  }

  return dateList
}

function shouldIncludeDate(date, repetition) {
  if (repetition.all) return true

  const weekOfMonth = getWeekOfMonth(date)

  switch (weekOfMonth) {
    case 1:
      return repetition.first
    case 2:
      return repetition.second
    case 3:
      return repetition.third
    case 4:
      return repetition.fourth
    case 5:
      return repetition.fifth
    default:
      return false
  }
}

export function getWeeklyOffDates(
  startDate,
  endDate,
  weeklyOff,
  holidays = [],
  repetition = {
    all: true,
    first: false,
    second: false,
    third: false,
    fourth: false,
    fifth: false,
  },
) {
  const dateList = getWeeklyOffDateList(
    startDate,
    endDate,
    weeklyOff,
    holidays,
    repetition,
  )
  return dateList.map((date, index) => ({
    description: weeklyOff.charAt(0).toUpperCase() + weeklyOff.slice(1),
    date: date,
    weekly_off: 1,
    idx: index + 1,
    repetition: repetition,
  }))
}
