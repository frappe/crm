import { describe, expect, it, vi } from 'vitest'

vi.mock('@/stores/users', () => ({
  usersStore: () => ({ getUser: () => ({}) }),
}))
vi.mock('@/utils/dialogs', () => ({ createDialog: vi.fn() }))

const { validateTimeRange, spanFrom, parseEventDoc, endDateFor, changeTime } =
  await import('@/composables/event')

describe('event form', () => {
  it('accepts a meeting that ends the next day', () => {
    const range = {
      fromDate: '2026-11-22',
      toDate: '2026-11-23',
      fromTime: '23:30',
      toTime: '00:00',
    }
    expect(validateTimeRange(range).valid).toBe(true)
    expect(validateTimeRange({ ...range, toDate: '2026-11-22' }).valid).toBe(
      false,
    )
  })

  it('keeps the days a meeting spans when it moves to another day', () => {
    const event = { fromDate: '2026-11-22', toDate: '2026-11-23' }
    expect(spanFrom(event, '2026-11-25')).toBe('2026-11-26')
    expect(
      spanFrom({ fromDate: '2026-11-22', toDate: '2026-11-22' }, '2026-11-25'),
    ).toBe('2026-11-25')
  })

  it('shows the Meet link without making it the location', () => {
    const doc = {
      name: 'EV1',
      starts_on: '2026-11-23 10:00:00',
      ends_on: '2026-11-23 10:30:00',
      google_meet_link: 'https://meet.google.com/abc',
    }
    expect(parseEventDoc(doc)).toMatchObject({
      location: '',
      meetLink: 'https://meet.google.com/abc',
    })
  })

  it('ends a meeting the next day only when its end time is before its start', () => {
    expect(endDateFor('2026-11-22', '10:00', '11:00')).toBe('2026-11-22')
    expect(endDateFor('2026-11-22', '23:30', '00:30')).toBe('2026-11-23')
    expect(endDateFor('2026-11-22', '10:00', '10:00')).toBe('2026-11-23')
  })

  it('ends an overnight meeting the same day once its start moves into the day', () => {
    const event = {
      fromDate: '2026-11-22',
      toDate: '2026-11-23',
      fromTime: '23:30',
      toTime: '00:30',
    }
    expect(changeTime(event, '10:00', true)).toBeNull()
    expect(event).toMatchObject({ toDate: '2026-11-22', toTime: '11:00' })
  })

  it('keeps the old end when the new one is invalid', () => {
    const event = {
      fromDate: '2026-11-22',
      toDate: '2026-11-22',
      fromTime: '10:00',
      toTime: '11:00',
    }
    expect(changeTime(event, '')).toBeTruthy()
    expect(event).toMatchObject({ toDate: '2026-11-22', toTime: '11:00' })
  })

  it('keeps the days a multi-day meeting spans when its time changes', () => {
    const event = {
      fromDate: '2026-11-22',
      toDate: '2026-11-25',
      fromTime: '10:00',
      toTime: '11:00',
    }
    expect(changeTime(event, '12:00')).toBeNull()
    expect(event).toMatchObject({ toDate: '2026-11-25', toTime: '12:00' })
  })
})
