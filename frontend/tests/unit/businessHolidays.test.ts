import { describe, expect, it } from 'vitest'
import {
  buildHolidays,
  emptyRepetition,
  getMonthWeeks,
  getRecurringDates,
  getRepetitionText,
  inferRecurringHolidays,
  reconcileWeeklyOffs,
} from '@/components/Settings/BusinessHolidays/utils'
import {
  holidayData,
  holidayDataErrors,
  removeHoliday,
  resetHolidayData,
  resetHolidayDataErrors,
} from '@/components/Settings/BusinessHolidays/store'
import type {
  Holiday,
  RecurringHoliday,
} from '@/components/Settings/BusinessHolidays/types'

describe('reconcileWeeklyOffs', () => {
  const weeklyOff = (date: string, description = 'Sunday'): Holiday => ({
    date,
    description,
    weekly_off: 1,
  })
  const marchSundays = [
    '2026-03-01',
    '2026-03-08',
    '2026-03-15',
    '2026-03-22',
    '2026-03-29',
  ].map((date) => weeklyOff(date))
  const reconcile = (holidays: Holiday[], rules: RecurringHoliday[] = []) =>
    reconcileWeeklyOffs(holidays, rules, '2026-03-01', '2026-03-31')

  it('infers an every-week rule when desk rows cover the whole range', () => {
    expect(reconcile(marchSundays)).toEqual({
      recurring_holidays: [everySunday],
      holidays: marchSundays,
    })
  })

  it('keeps desk rows for only some weeks as single holidays', () => {
    const rows = [
      weeklyOff('2026-03-14', 'Saturday'),
      weeklyOff('2026-03-28', 'Saturday'),
    ]
    const form = reconcile(rows)
    expect(form.recurring_holidays).toEqual([])
    expect(form.holidays).toEqual(
      rows.map((row) => ({ ...row, weekly_off: 0 })),
    )
    expect(
      buildHolidays(
        form.holidays,
        form.recurring_holidays,
        '2026-03-01',
        '2026-03-31',
      ).map((row) => row.date),
    ).toEqual(['2026-03-14', '2026-03-28'])
  })

  it('keeps a stored rule that matches its rows, around a single holiday', () => {
    const rows = [
      ...marchSundays.filter((row) => row.date !== '2026-03-08'),
      { date: '2026-03-08', description: 'Holi', weekly_off: 0 as const },
    ]
    expect(reconcile(rows, [everySunday]).recurring_holidays).toEqual([
      everySunday,
    ])
  })

  it('drops a stored rule when a row was deleted in desk', () => {
    const rows = marchSundays.filter((row) => row.date !== '2026-03-15')
    const form = reconcile(rows, [everySunday])
    expect(form.recurring_holidays).toEqual([])
    expect(form.holidays.map((row) => row.date)).toEqual(
      rows.map((row) => row.date),
    )
  })

  it('keeps a weekly-off row added in desk for a day with no rule', () => {
    const extra = weeklyOff('2026-03-07', 'Saturday')
    const form = reconcile([...marchSundays, extra], [everySunday])
    expect(form.recurring_holidays).toEqual([everySunday])
    expect(form.holidays).toContainEqual({ ...extra, weekly_off: 0 })
  })
})

describe('holidays error', () => {
  it('clears once the holiday outside the range is removed', () => {
    resetHolidayData()
    resetHolidayDataErrors()
    Object.assign(holidayData.value, {
      from_date: '2026-03-01',
      to_date: '2026-03-31',
      holidays: [{ date: '2026-03-10', description: 'Holi', weekly_off: 0 }],
    })
    holidayDataErrors.value.holidays = 'Holi is outside the date range'

    removeHoliday(holidayData.value.holidays[0])

    expect(holidayDataErrors.value.holidays).toBe('')
  })
})

const everySunday: RecurringHoliday = {
  day: 'Sunday',
  repetition: { ...emptyRepetition(), all: true },
}
const secondAndFourthSaturday: RecurringHoliday = {
  day: 'Saturday',
  repetition: { ...emptyRepetition(), second: true, fourth: true },
}

describe('getRecurringDates', () => {
  it('lists every matching weekday inside the range', () => {
    expect(getRecurringDates('2026-03-01', '2026-03-31', everySunday)).toEqual([
      '2026-03-01',
      '2026-03-08',
      '2026-03-15',
      '2026-03-22',
      '2026-03-29',
    ])
  })

  it('keeps only the chosen weeks of the month', () => {
    // March 2026 Saturdays: 7, 14, 21, 28.
    expect(
      getRecurringDates('2026-03-01', '2026-04-30', secondAndFourthSaturday),
    ).toEqual(['2026-03-14', '2026-03-28', '2026-04-11', '2026-04-25'])
  })

  it('counts the fifth week from day 29', () => {
    const fifthSunday: RecurringHoliday = {
      day: 'Sunday',
      repetition: { ...emptyRepetition(), fifth: true },
    }
    expect(getRecurringDates('2026-03-01', '2026-05-31', fifthSunday)).toEqual([
      '2026-03-29',
      '2026-05-31',
    ])
  })
})

describe('buildHolidays', () => {
  it('replaces weekly offs and keeps single holidays, sorted by date', () => {
    const holidays = buildHolidays(
      [
        { date: '2026-03-10', description: 'Founders Day', weekly_off: 0 },
        { date: '2026-03-02', description: 'Monday', weekly_off: 1 },
      ],
      [everySunday],
      '2026-03-01',
      '2026-03-15',
    )
    expect(holidays).toEqual([
      { date: '2026-03-01', description: 'Sunday', weekly_off: 1 },
      { date: '2026-03-08', description: 'Sunday', weekly_off: 1 },
      { date: '2026-03-10', description: 'Founders Day', weekly_off: 0 },
      { date: '2026-03-15', description: 'Sunday', weekly_off: 1 },
    ])
  })

  it('lets a single holiday win over a weekly off on the same date', () => {
    const holidays = buildHolidays(
      [{ date: '2026-03-08', description: 'Holi', weekly_off: 0 }],
      [everySunday],
      '2026-03-08',
      '2026-03-08',
    )
    expect(holidays).toEqual([
      { date: '2026-03-08', description: 'Holi', weekly_off: 0 },
    ])
  })

  it('drops weekly offs while the range is incomplete or reversed', () => {
    const single = { date: '2026-03-10', description: 'Holi', weekly_off: 0 }
    expect(buildHolidays([single], [everySunday], '', '2026-03-31')).toEqual([
      single,
    ])
    expect(
      buildHolidays([single], [everySunday], '2026-04-01', '2026-03-01'),
    ).toEqual([single])
  })
})

describe('getRepetitionText', () => {
  it('describes every week and chosen weeks', () => {
    expect(getRepetitionText(everySunday.repetition)).toBe('Every week')
    expect(getRepetitionText(secondAndFourthSaturday.repetition)).toBe(
      'Every second and fourth week',
    )
    expect(
      getRepetitionText({
        ...emptyRepetition(),
        first: true,
        third: true,
        fifth: true,
      }),
    ).toBe('Every first, third and fifth week')
  })
})

describe('inferRecurringHolidays', () => {
  it('turns weekly-off rows from desk into every-week rules', () => {
    expect(
      inferRecurringHolidays([
        { date: '2026-03-01', description: 'Sunday', weekly_off: 1 },
        { date: '2026-03-08', description: 'Sunday', weekly_off: 1 },
        { date: '2026-03-07', description: 'Saturday', weekly_off: 1 },
        { date: '2026-03-10', description: 'Holi', weekly_off: 0 },
      ]),
    ).toEqual([
      { day: 'Saturday', repetition: { ...emptyRepetition(), all: true } },
      everySunday,
    ])
  })
})

describe('getMonthWeeks', () => {
  it('lays the month out in six Sunday-first weeks', () => {
    // February 2026 starts on a Sunday and has 28 days.
    const weeks = getMonthWeeks(2026, 1)
    expect(weeks).toHaveLength(6)
    expect(weeks[0][0]).toBe('2026-02-01')
    expect(weeks[3][6]).toBe('2026-02-28')
    expect(weeks[4].every((date) => date === null)).toBe(true)
  })
})
