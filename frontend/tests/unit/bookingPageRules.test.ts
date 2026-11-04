import { describe, expect, it } from 'vitest'
import {
  copyHours,
  embedSnippet,
  endTimeOptions,
  googleConnectHref,
  hoursErrors,
  hoursFor,
  invalidEmbeddingDomains,
  moveStart,
  nextRange,
  type HoursRow,
} from '@/components/Settings/BookingPages/bookingPageRules'

const row = (workday: string, start_time: string, end_time: string) => ({
  workday,
  start_time,
  end_time,
})

describe('booking page weekly hours', () => {
  it('lists a day’s rows earliest first', () => {
    const rows = [
      row('Monday', '14:00:00', '18:00:00'),
      row('Tuesday', '09:00:00', '17:00:00'),
      row('Monday', '9:00:00', '12:00:00'),
    ]
    expect(hoursFor(rows, 'Monday').map((r) => r.start_time)).toEqual([
      '9:00:00',
      '14:00:00',
    ])
  })

  it('flags an end before the start, and overlapping ranges', () => {
    const backwards = row('Monday', '17:00:00', '09:00:00')
    const first = row('Tuesday', '09:00:00', '13:00:00')
    const overlapping = row('Tuesday', '12:00:00', '15:00:00')
    const fine = row('Wednesday', '09:00:00', '12:00:00')
    const errors = hoursErrors(
      [backwards, first, overlapping, fine],
      ['Monday', 'Tuesday', 'Wednesday'],
    )
    expect(errors.get(backwards)).toBe('End time must be after the start time')
    expect(errors.get(overlapping)).toBe(
      'Times overlap with another set of times',
    )
    expect(errors.has(first)).toBe(false)
    expect(errors.has(fine)).toBe(false)
  })

  it('lets a range start where the last one ends', () => {
    const rows = [
      row('Monday', '09:00:00', '12:00:00'),
      row('Monday', '12:00:00', '17:00:00'),
    ]
    expect(hoursErrors(rows, ['Monday']).size).toBe(0)
  })

  it('offers end times after the start, with the length, like Google', () => {
    const options = endTimeOptions('09:00:00')
    expect(options[0]).toEqual({ value: '09:15', label: '9:15 am (15 mins)' })
    expect(options[3]).toEqual({ value: '10:00', label: '10:00 am (1 hr)' })
    expect(options.find((o) => o.value === '10:30')?.label).toBe(
      '10:30 am (1.5 hrs)',
    )
    expect(options.at(-1)?.value).toBe('23:45')
  })

  it('pushes the end along when the start moves past it, keeping the length', () => {
    const range = row('Monday', '09:00:00', '11:00:00')
    expect(moveStart(range, '10:00')).toEqual({ start_time: '10:00:00' })
    expect(moveStart(range, '12:00')).toEqual({
      start_time: '12:00:00',
      end_time: '14:00:00',
    })
    // never past the end of the day
    expect(moveStart(range, '23:45').start_time).toBe('23:30:00')
  })

  it('adds the next range an hour after the day’s last one', () => {
    expect(nextRange()).toEqual(['09:00:00', '11:00:00'])
    expect(nextRange(row('Monday', '09:00:00', '12:00:00'))).toEqual([
      '13:00:00',
      '15:00:00',
    ])
    expect(nextRange(row('Monday', '20:00:00', '23:00:00'))).toEqual([
      '22:00:00',
      '23:00:00',
    ])
  })

  it('copies a day’s hours to other days, replacing theirs', () => {
    const rows: HoursRow[] = [
      row('Monday', '09:00:00', '12:00:00'),
      row('Monday', '13:00:00', '17:00:00'),
      row('Tuesday', '10:00:00', '11:00:00'),
      row('Friday', '09:00:00', '17:00:00'),
    ]
    const copied = copyHours(rows, 'Monday', ['Tuesday', 'Wednesday'], row)
    expect(hoursFor(copied, 'Tuesday')).toEqual([
      row('Tuesday', '09:00:00', '12:00:00'),
      row('Tuesday', '13:00:00', '17:00:00'),
    ])
    expect(hoursFor(copied, 'Wednesday')).toHaveLength(2)
    expect(hoursFor(copied, 'Monday')).toHaveLength(2)
    expect(hoursFor(copied, 'Friday')).toEqual([
      row('Friday', '09:00:00', '17:00:00'),
    ])
  })
})

describe('booking page sharing', () => {
  it('builds embed code that sizes the iframe to the page', () => {
    const code = embedSnippet(
      'https://acme.frappe.cloud/crm-book/demo',
      'demo',
      'Product demo',
    )
    expect(code).toContain(
      '<iframe id="crm-book-demo" src="https://acme.frappe.cloud/crm-book/demo?embed=1"',
    )
    expect(code).toContain('title="Product demo"')
    // only height messages from the CRM site, for this page, are trusted
    expect(code).toContain('e.origin === "https://acme.frappe.cloud"')
    expect(code).toContain('e.data.route === "demo"')
    expect(code.trim().endsWith('</script>')).toBe(true)
  })

  it('flags allowed domains the server would drop', () => {
    expect(
      invalidEmbeddingDomains(
        'https://www.example.com\nhttp://localhost:8199  *.acme.com',
      ),
    ).toEqual([])
    expect(
      invalidEmbeddingDomains('example.com/path javascript:alert(1)'),
    ).toEqual(['example.com/path', 'javascript:alert(1)'])
    expect(invalidEmbeddingDomains(undefined)).toEqual([])
  })
})

describe('connecting Google Calendar', () => {
  it('opens the host’s existing calendar record', () => {
    expect(googleConnectHref('My Calendar', 'sarah@example.com', 'Sarah')).toBe(
      '/app/google-calendar/My%20Calendar',
    )
  })

  it('opens a new record filled in for the host', () => {
    const href = googleConnectHref(null, 'sarah@example.com', 'Sarah Chen')
    const params = new URLSearchParams(href.split('?')[1])
    expect(href.startsWith('/app/google-calendar/new?')).toBe(true)
    expect(params.get('user')).toBe('sarah@example.com')
    expect(params.get('calendar_name')).toBe('Sarah Chen')
    expect(params.get('push_to_google_calendar')).toBe('1')
    expect(params.get('pull_from_google_calendar')).toBe('1')
  })
})
