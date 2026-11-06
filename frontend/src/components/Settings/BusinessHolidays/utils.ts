import { dayjs } from 'frappe-ui'
import type {
  Holiday,
  HolidayListForm,
  RecurringHoliday,
  RepetitionPattern,
  Weekday,
} from './types'

export const WEEKDAYS: Weekday[] = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

// dayjs numbers the week from Sunday.
const DAY_INDEX: Record<Weekday, number> = {
  Sunday: 0,
  Monday: 1,
  Tuesday: 2,
  Wednesday: 3,
  Thursday: 4,
  Friday: 5,
  Saturday: 6,
}

const WEEKS = ['first', 'second', 'third', 'fourth', 'fifth'] as const

export const DATE_FORMAT = 'YYYY-MM-DD'

export function emptyRepetition(): RepetitionPattern {
  return {
    all: false,
    first: false,
    second: false,
    third: false,
    fourth: false,
    fifth: false,
  }
}

export function hasRepetition(repetition: RepetitionPattern): boolean {
  return repetition.all || WEEKS.some((week) => repetition[week])
}

export function getRepetitionText(repetition: RepetitionPattern): string {
  if (repetition.all) return __('Every week')

  const labels: Record<(typeof WEEKS)[number], string> = {
    first: __('first'),
    second: __('second'),
    third: __('third'),
    fourth: __('fourth'),
    fifth: __('fifth'),
  }
  const weeks = WEEKS.filter((week) => repetition[week]).map((w) => labels[w])
  if (!weeks.length) return ''

  const last = weeks.pop() as string
  const text = weeks.length ? __('{0} and {1}', [weeks.join(', '), last]) : last
  return __('Every {0} week', [text])
}

// Which occurrence of its weekday the date is, so the 1st to 7th is always the first.
export function getWeekOfMonth(date: string): number {
  return Math.ceil(dayjs(date).date() / 7)
}

// Dates in the range that fall on the rule's weekday and weeks of the month.
export function getRecurringDates(
  fromDate: string,
  toDate: string,
  rule: RecurringHoliday,
): string[] {
  const start = dayjs(fromDate)
  const end = dayjs(toDate)
  let current = start.day(DAY_INDEX[rule.day])
  if (current.isBefore(start, 'day')) current = current.add(1, 'week')

  const dates: string[] = []
  while (!current.isAfter(end, 'day')) {
    const date = current.format(DATE_FORMAT)
    const week = WEEKS[getWeekOfMonth(date) - 1]
    if (rule.repetition.all || rule.repetition[week]) dates.push(date)
    current = current.add(1, 'week')
  }
  return dates
}

// Rebuilds the weekly-off rows from the rules; a single holiday wins over a rule on the same date.
export function buildHolidays(
  holidays: Holiday[],
  rules: RecurringHoliday[],
  fromDate: string,
  toDate: string,
): Holiday[] {
  const singles = holidays.filter((holiday) => !holiday.weekly_off)
  const rows = [...singles]

  if (fromDate && toDate && fromDate <= toDate) {
    const taken = new Set(singles.map((holiday) => holiday.date))
    for (const rule of rules) {
      for (const date of getRecurringDates(fromDate, toDate, rule)) {
        if (taken.has(date)) continue
        taken.add(date)
        rows.push({ date, description: __(rule.day), weekly_off: 1 })
      }
    }
  }
  return sortHolidays(rows)
}

export function sortHolidays(holidays: Holiday[]): Holiday[] {
  return [...holidays].sort((a, b) => a.date.localeCompare(b.date))
}

// Lists made in desk have weekly-off rows but no rules, so each weekday they cover becomes an every-week rule.
export function inferRecurringHolidays(
  holidays: Holiday[],
): RecurringHoliday[] {
  const days = new Set(
    holidays
      .filter((holiday) => holiday.weekly_off)
      .map((holiday) => dayjs(holiday.date).day()),
  )
  return WEEKDAYS.filter((day) => days.has(DAY_INDEX[day])).map((day) => ({
    day,
    repetition: { ...emptyRepetition(), all: true },
  }))
}

// A rule rebuilds its weekday's rows on the next edit, and SLAs read those rows.
// So a rule that would change them is dropped, and its rows stay as single holidays.
export function reconcileWeeklyOffs(
  holidays: Holiday[],
  storedRules: RecurringHoliday[],
  fromDate: string,
  toDate: string,
): Pick<HolidayListForm, 'holidays' | 'recurring_holidays'> {
  const singles = new Set(
    holidays.filter((row) => !row.weekly_off).map((row) => row.date),
  )
  const weeklyOffs = holidays
    .filter((row) => row.weekly_off && !singles.has(row.date))
    .map((row) => row.date)

  const candidates = storedRules.length
    ? storedRules
    : inferRecurringHolidays(holidays)
  const rules = candidates.filter((rule) => {
    const expected = getRecurringDates(fromDate, toDate, rule).filter(
      (date) => !singles.has(date),
    )
    const actual = weeklyOffs.filter(
      (date) => dayjs(date).day() === DAY_INDEX[rule.day],
    )
    return (
      expected.length === actual.length &&
      expected.every((date) => actual.includes(date))
    )
  })

  const covered = new Set(rules.map((rule) => DAY_INDEX[rule.day]))
  return {
    recurring_holidays: rules,
    holidays: holidays.map((row) =>
      row.weekly_off && !covered.has(dayjs(row.date).day())
        ? { ...row, weekly_off: 0 }
        : row,
    ),
  }
}

// Six weeks of seven days, Sunday first; days outside the month are null.
export function getMonthWeeks(
  year: number,
  month: number,
): (string | null)[][] {
  const first = dayjs(new Date(year, month, 1))
  const start = first.subtract(first.day(), 'day')
  return Array.from({ length: 6 }, (_, week) =>
    Array.from({ length: 7 }, (_, day) => {
      const date = start.add(week * 7 + day, 'day')
      return date.month() === month ? date.format(DATE_FORMAT) : null
    }),
  )
}
