import { describe, expect, it } from 'vitest'
import {
  buildHolidays,
  emptyRepetition,
  getMonthWeeks,
  getRecurringDates,
  getRepetitionText,
  inferRecurringHolidays,
} from '@/components/Settings/BusinessHolidays/utils'
import type { RecurringHoliday } from '@/components/Settings/BusinessHolidays/types'

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
