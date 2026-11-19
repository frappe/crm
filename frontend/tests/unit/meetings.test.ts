import {
  hasEnded,
  isOngoing,
  meetingLink,
  meetingTime,
  meetingUntil,
} from '@/utils/meetings'
import { dayjs } from 'frappe-ui'

const meeting = (fields = {}) => ({
  name: 'EV-1',
  starts_on: '2026-11-19 10:00:00',
  ends_on: '2026-11-19 11:00:00',
  ...fields,
})

describe('meetingLink', () => {
  it('prefers a link in the location over the Meet link', () => {
    const link = meetingLink(
      meeting({
        location: 'https://zoom.us/j/1',
        google_meet_link: 'https://meet.google.com/abc',
      }),
    )
    expect(link).toBe('https://zoom.us/j/1')
  })

  it('falls back to the Meet link when the location is a place', () => {
    expect(meetingLink(meeting({ location: '' }))).toBeNull()
    expect(
      meetingLink(meeting({ google_meet_link: 'https://meet.google.com/abc' })),
    ).toBe('https://meet.google.com/abc')
    expect(meetingLink(meeting({ location: 'Office, 2nd floor' }))).toBeNull()
  })
})

describe('meetingTime', () => {
  it('names all-day meetings', () => {
    expect(meetingTime(meeting({ all_day: 1 }))).toBe('All day')
  })
})

describe('meetingUntil', () => {
  it('names only the end time', () => {
    expect(meetingUntil(meeting())).toMatch(/^until \d{1,2}:\d{2} (am|pm)$/)
  })
})

describe('isOngoing', () => {
  const now = dayjs('2026-11-19 10:30:00')

  it('is true only between start and end', () => {
    expect(isOngoing(meeting(), now)).toBe(true)
    expect(isOngoing(meeting(), dayjs('2026-11-19 11:00:00'))).toBe(false)
    expect(isOngoing(meeting(), dayjs('2026-11-19 09:59:00'))).toBe(false)
  })

  it('is never true for all-day meetings', () => {
    expect(isOngoing(meeting({ all_day: 1 }), now)).toBe(false)
  })
})

describe('hasEnded', () => {
  it('is true once the end has passed, never for all-day meetings', () => {
    expect(hasEnded(meeting(), dayjs('2026-11-19 11:00:00'))).toBe(true)
    expect(hasEnded(meeting(), dayjs('2026-11-19 10:59:00'))).toBe(false)
    expect(hasEnded(meeting({ all_day: 1 }), dayjs('2026-11-20'))).toBe(false)
  })
})
