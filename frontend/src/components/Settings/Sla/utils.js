import { ref } from 'vue'
import { validateConditions } from '../../../utils'

const working_hours = [
  {
    workday: 'Monday',
    start_time: '09:00:00',
    end_time: '17:00:00',
  },
  {
    workday: 'Tuesday',
    start_time: '09:00:00',
    end_time: '17:00:00',
  },
  {
    workday: 'Wednesday',
    start_time: '09:00:00',
    end_time: '17:00:00',
  },
  {
    workday: 'Thursday',
    start_time: '09:00:00',
    end_time: '17:00:00',
  },
  {
    workday: 'Friday',
    start_time: '09:00:00',
    end_time: '17:00:00',
  },
]

export const slaData = ref({
  name: '',
  sla_name: '',
  apply_on: 'CRM Lead',
  enabled: true,
  default: false,
  rolling_responses: false,
  start_date: '',
  end_date: '',
  condition: [],
  condition_json: [],
  priorities: [],
  holiday_list: '',
  working_hours: working_hours,
})

export const resetSlaData = () => {
  slaData.value = {
    name: '',
    sla_name: '',
    apply_on: 'CRM Lead',
    enabled: true,
    default: false,
    rolling_responses: false,
    start_date: '',
    end_date: '',
    condition: [],
    condition_json: [],
    priorities: [],
    holiday_list: '',
    working_hours: working_hours,
  }
}

export const slaDataErrors = ref({
  sla_name: '',
  enabled: '',
  default_sla: '',
  apply_sla_for_resolution: '',
  priorities: '',
  holiday_list: '',
  default_priority: '',
  start_date: '',
  end_date: '',
  working_hours: '',
  condition: '',
})

export const resetSlaDataErrors = () => {
  slaDataErrors.value = {
    sla_name: '',
    enabled: '',
    default_sla: '',
    apply_sla_for_resolution: '',
    priorities: '',
    holiday_list: '',
    default_priority: '',
    start_date: '',
    end_date: '',
    working_hours: '',
    condition: '',
  }
}

export function validateSlaData(key, skipConditionCheck = false) {
  // Reset all errors
  resetSlaDataErrors()

  const validateField = (field) => {
    if (key && field !== key) return

    switch (field) {
      case 'sla_name':
        if (!slaData.value.sla_name?.trim()) {
          slaDataErrors.value.sla_name = __('SLA policy name is required')
        } else {
          slaDataErrors.value.sla_name = ''
        }
        break
      case 'priorities':
        if (
          !Array.isArray(slaData.value.priorities) ||
          slaData.value.priorities.length === 0
        ) {
          slaDataErrors.value.priorities = __(
            'At least one priority is required',
          )
        } else {
          const prioritiesError = []
          slaData.value.priorities.forEach((priority, index) => {
            const priorityNum = index + 1
            if (!priority.priority?.trim()) {
              prioritiesError.push(
                __('Priority {0}: Priority name is required', [priorityNum]),
              )
            }
            if (
              !priority.first_response_time ||
              priority.first_response_time == 0
            ) {
              prioritiesError.push(
                __('Priority {0}: Response time is required', [priorityNum]),
              )
            }
          })

          // Check for duplicate priorities
          const priorityNames = slaData.value.priorities
            .map((p) => p.priority?.trim().toLowerCase())
            .filter(Boolean)
          const uniquePriorities = new Set(priorityNames)

          if (priorityNames.length !== uniquePriorities.size) {
            prioritiesError.push(__('Priorities must be unique'))
          }

          if (prioritiesError.length > 0) {
            slaDataErrors.value.priorities = prioritiesError.join(', ')
          } else {
            slaDataErrors.value.priorities = ''
          }
        }
        break
      case 'start_date':
        if (
          slaData.value.end_date &&
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.start_date = __(
            'Start date cannot be after end date',
          )
        } else {
          slaDataErrors.value.start_date = ''
        }
        break
      case 'end_date':
        if (
          slaData.value.start_date &&
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.end_date = __(
            'End date cannot be before start date',
          )
        } else {
          slaDataErrors.value.end_date = ''
        }
        break
      case 'condition':
        if (skipConditionCheck) {
          break
        }
        if (
          slaData.value.condition_json.length > 0 &&
          !validateConditions(slaData.value.condition_json)
        ) {
          slaDataErrors.value.condition = __('Valid conditions are required')
        } else {
          slaDataErrors.value.condition = ''
        }
        break
      case 'working_hours':
        const validWorkdays = slaData.value.working_hours?.filter(
          (day) =>
            day.workday &&
            day.workday.trim() !== '' &&
            day.start_time &&
            day.end_time &&
            day.start_time.trim() !== '' &&
            day.end_time.trim() !== '',
        )

        if (!validWorkdays?.length) {
          slaDataErrors.value.working_hours = __(
            'At least one valid workday with workday, start time, and end time is required',
          )
        } else {
          // Check for duplicate workdays
          const workdayMap = new Map()
          const duplicateWorkdays = []

          for (const day of validWorkdays) {
            if (workdayMap.has(day.workday)) {
              duplicateWorkdays.push(day.workday)
            } else {
              workdayMap.set(day.workday, true)
            }
          }

          if (duplicateWorkdays.length > 0) {
            slaDataErrors.value.working_hours = __(
              `Duplicate workday found: {0}. Each workday should be unique.`,
              [duplicateWorkdays.join(', ')],
            )
            return slaDataErrors.value
          } else {
            slaDataErrors.value.working_hours = ''
          }

          const invalidTimeRanges = []
          for (const day of validWorkdays) {
            const startTimeStr = day.start_time.trim()
            const endTimeStr = day.end_time.trim()

            const parseTime = (timeStr) => {
              const [hours, minutes] = timeStr.split(':').map(Number)
              const date = new Date()
              date.setHours(hours, minutes || 0, 0, 0)
              return date
            }

            try {
              const startTime = parseTime(startTimeStr)
              const endTime = parseTime(endTimeStr)

              if (startTime >= endTime) {
                invalidTimeRanges.push(
                  `${day.workday} (${startTimeStr} - ${endTimeStr})`,
                )
              }
            } catch (error) {
              // If time parsing fails, mark as invalid
              invalidTimeRanges.push(
                __(`{0} (Invalid time format)`, [day.workday]),
              )
            }
          }

          if (invalidTimeRanges.length > 0) {
            slaDataErrors.value.working_hours = __(
              `End time must be after start time for: {0}`,
              [invalidTimeRanges.join(', ')],
            )
          } else {
            slaDataErrors.value.working_hours = ''
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
    Object.keys(slaDataErrors.value).forEach(validateField)
  }

  return slaDataErrors.value
}
