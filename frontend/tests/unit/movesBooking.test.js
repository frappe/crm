import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { setConfig } from 'frappe-ui'

vi.mock('@/stores/users', () => ({ usersStore: () => ({}) }))
vi.mock('@/utils/dialogs', () => ({ createDialog: vi.fn() }))

const { movesBooking } = await import('@/composables/event')

// The booking is stored in system time; the form edits it in the CRM user's
// timezone, which needn't be the browser's.
describe('movesBooking', () => {
  const booking = {
    guest: 'vera@example.com',
    startsOn: '2026-11-23 10:00:00',
    endsOn: '2026-11-23 10:30:00',
  }

  beforeEach(() => {
    setConfig('systemTimezone', 'Asia/Kolkata')
    setConfig('localTimezone', 'America/New_York')
  })

  afterEach(() => {
    setConfig('systemTimezone', null)
    setConfig('localTimezone', null)
  })

  it('sees an unchanged meeting as not moved', () => {
    const edited = {
      fromDate: '2026-11-22',
      fromTime: '23:30',
      toDate: '2026-11-23',
      toTime: '00:00',
    }
    expect(movesBooking(booking, edited)).toBe(false)
  })

  it('sees a new time as moved', () => {
    const edited = {
      fromDate: '2026-11-23',
      fromTime: '00:00',
      toDate: '2026-11-23',
      toTime: '00:30',
    }
    expect(movesBooking(booking, edited)).toBe(true)
  })

  it('treats a meeting without a booking as never moved', () => {
    expect(
      movesBooking(null, { fromDate: '2026-11-23', fromTime: '09:00' }),
    ).toBe(false)
  })
})
