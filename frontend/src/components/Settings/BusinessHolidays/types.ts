import type { createListResource } from 'frappe-ui'

export type Weekday =
  | 'Monday'
  | 'Tuesday'
  | 'Wednesday'
  | 'Thursday'
  | 'Friday'
  | 'Saturday'
  | 'Sunday'

export interface RepetitionPattern {
  all: boolean
  first: boolean
  second: boolean
  third: boolean
  fourth: boolean
  fifth: boolean
}

export interface RecurringHoliday {
  day: Weekday
  repetition: RepetitionPattern
}

// A CRM Holiday row; dates are kept as YYYY-MM-DD strings throughout.
export interface Holiday {
  date: string
  description: string
  weekly_off: 0 | 1
}

// A CRM Holiday List as frappe.client.get returns it.
export interface HolidayListDoc {
  name: string
  holiday_list_name: string
  description?: string | null
  from_date: string
  to_date: string
  total_holidays?: number
  holidays: Holiday[]
  recurring_holidays?: string | null
}

// A row of the holiday list overview.
export interface HolidayListRow {
  name: string
  description?: string | null
  from_date: string
  to_date: string
  total_holidays: number
}

export type HolidayListResource = ReturnType<
  typeof createListResource<HolidayListRow>
>

export interface HolidayListForm {
  // Empty until the list is saved.
  name: string
  holiday_list_name: string
  description: string
  from_date: string
  to_date: string
  holidays: Holiday[]
  recurring_holidays: RecurringHoliday[]
}

export interface HolidayErrors {
  holiday_list_name: string
  from_date: string
  to_date: string
  holidays: string
}

export interface HolidayModalState {
  show: boolean
  date: string
  description: string
  // The row being edited, null when adding.
  editing: Holiday | null
}
