import { setConfig } from 'frappe-ui'
import {
  formatTaskDue,
  fromAllDayDueDate,
  isTaskOverdue,
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
