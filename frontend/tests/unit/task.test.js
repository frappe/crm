import { setConfig } from 'frappe-ui'
import {
  followUpPresets,
  formatTaskDue,
  fromAllDayDueDate,
  isTaskOverdue,
  nextFollowUp,
  relativeTaskDue,
  toAllDayDueDate,
} from '@/utils/task'

describe('task due dates', () => {
  beforeEach(() => {
    setConfig('systemTimezone', 'UTC')
    setConfig('localTimezone', 'Asia/Kolkata')
    vi.useFakeTimers()
    // 00:30 on 24 Oct in Asia/Kolkata
    vi.setSystemTime(new Date('2026-10-23T19:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
    setConfig('systemTimezone', null)
    setConfig('localTimezone', null)
  })

  it('marks a timed task overdue once its time passes', () => {
    expect(isTaskOverdue({ due_date: '2026-10-23 18:59:00' })).toBe(true)
    expect(isTaskOverdue({ due_date: '2026-10-23 19:01:00' })).toBe(false)
  })

  it('marks an all-day task overdue from the next local day', () => {
    const yesterday = { due_date: '2026-10-23 00:00:00', all_day: 1 }
    const today = { due_date: '2026-10-24 00:00:00', all_day: 1 }
    expect(isTaskOverdue(yesterday)).toBe(true)
    expect(isTaskOverdue(today)).toBe(false)
  })

  it('never marks closed tasks overdue', () => {
    expect(
      isTaskOverdue({ due_date: '2026-10-01 10:00:00', status: 'Done' }),
    ).toBe(false)
  })

  it('labels due dates relative to the local day', () => {
    const allDay = (date) => relativeTaskDue({ due_date: date, all_day: 1 })
    const timed = (date) => relativeTaskDue({ due_date: date })
    expect(allDay('2026-10-22 00:00:00')).toBe('2d overdue')
    expect(timed('2026-10-23 18:00:00')).toBe('1d overdue')
    expect(timed('2026-10-23 18:59:00')).toBe('Overdue')
    expect(allDay('2026-10-24 00:00:00')).toBe('Today')
    expect(timed('2026-10-24 04:30:00')).toBe('10:00 am')
    expect(allDay('2026-10-25 00:00:00')).toBe('Tomorrow')
    expect(allDay('2026-10-29 00:00:00')).toBe('Thu')
    expect(allDay('2026-11-05 00:00:00')).toBe('5 Nov')
    expect(relativeTaskDue({ due_date: null })).toBe('')
  })

  it('shows all-day tasks without a time or timezone shift', () => {
    const task = { due_date: '2026-10-24 00:00:00', all_day: 1 }
    expect(formatTaskDue(task)).toBe('24 Oct')
    expect(formatTaskDue({ due_date: '2026-10-23 19:00:00' })).toBe(
      '24 Oct, 12:30 am',
    )
  })

  it('keeps the local day when toggling all day', () => {
    expect(toAllDayDueDate('2026-10-23 19:00:00')).toBe('2026-10-24')
    expect(fromAllDayDueDate('2026-10-24')).toBe('2026-10-23 18:30:00')
  })
})

describe('follow-up presets', () => {
  beforeEach(() => {
    setConfig('systemTimezone', 'UTC')
    setConfig('localTimezone', 'Asia/Kolkata')
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    setConfig('systemTimezone', null)
    setConfig('localTimezone', null)
  })

  function presetDates() {
    return Object.fromEntries(followUpPresets().map((p) => [p.key, p.date]))
  }

  it('counts days from the local day, not the system day', () => {
    // Fri 23 Oct in UTC, already Sat 24 Oct in Asia/Kolkata
    vi.setSystemTime(new Date('2026-10-23T19:00:00Z'))
    expect(presetDates()).toEqual({
      today: '2026-10-24',
      tomorrow: '2026-10-25',
      in_3_days: '2026-10-27',
      next_week: '2026-10-26',
    })
  })

  it('takes next week as the coming Monday', () => {
    // Sun 25 Oct
    vi.setSystemTime(new Date('2026-10-25T06:00:00Z'))
    expect(presetDates().next_week).toBe('2026-10-26')
  })

  it('skips to the following Monday on a Monday', () => {
    // Mon 26 Oct
    vi.setSystemTime(new Date('2026-10-26T06:00:00Z'))
    expect(presetDates().next_week).toBe('2026-11-02')
  })
})

describe('next follow-up', () => {
  beforeEach(() => {
    setConfig('systemTimezone', 'UTC')
    setConfig('localTimezone', 'Asia/Kolkata')
  })

  afterEach(() => {
    setConfig('systemTimezone', null)
    setConfig('localTimezone', null)
  })

  it('picks the earliest open dated task', () => {
    const tasks = [
      { name: 'later', due_date: '2026-10-26 00:00:00', all_day: 1 },
      { name: 'done', due_date: '2026-10-20 00:00:00', status: 'Done' },
      { name: 'undated' },
      // 25 Oct, 09:30 in Asia/Kolkata
      { name: 'timed', due_date: '2026-10-25 04:00:00' },
      { name: 'all_day', due_date: '2026-10-25 00:00:00', all_day: 1 },
    ]
    expect(nextFollowUp(tasks).name).toBe('all_day')
    expect(nextFollowUp(tasks.slice(0, 4)).name).toBe('timed')
  })

  it('returns nothing without an open dated task', () => {
    expect(nextFollowUp([{ name: 'undated' }])).toBeUndefined()
    expect(nextFollowUp()).toBeUndefined()
  })
})
