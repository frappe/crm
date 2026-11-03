import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MockDevice } from '../../../crm/fcrm/frontend/telephony/mockTwilioDevice.js'
import { createTwilioCall, formatClock } from '../../../crm/fcrm/frontend/telephony/twilioCall.js'

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

function setup(contact = { full_name: 'Alice Johnson', lead: 'CRM-LEAD-1', name: 'C-1' }) {
  const api = {
    token: vi.fn().mockResolvedValue({ token: 't', mock: true }),
    contact: vi.fn().mockResolvedValue(contact),
    link: vi.fn().mockResolvedValue(null),
  }
  const call = createTwilioCall({ api, loadDevice: async () => MockDevice })
  return { api, call }
}

beforeEach(() => vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] }))
afterEach(() => {
  vi.useRealTimers()
  delete window.__crmTelephonyMock
})

describe('an incoming call', () => {
  it('rings, resolves the caller to the lead, then runs the clock once accepted', async () => {
    const { call } = setup()
    await call.start()

    window.__crmTelephonyMock.twilio.ring({ from: '+15550100101' })
    expect(call.state.step).toBe('incoming')
    expect(call.isLive()).toBe(true)
    await vi.waitFor(() => expect(call.state.contact.name).toBe('Alice Johnson'))
    expect(call.state.contact.record).toEqual({ doctype: 'CRM Lead', name: 'CRM-LEAD-1' })

    call.accept()
    expect(call.state.step).toBe('oncall')
    vi.advanceTimersByTime(65_000)
    expect(call.state.seconds).toBe(65)
  })

  it('goes back to idle when rejected or when the caller gives up', async () => {
    const { call } = setup()
    await call.start()
    const device = window.__crmTelephonyMock.twilio

    device.ring({ from: '+1' })
    call.reject()
    expect(call.state.step).toBe('idle')
    expect(call.state.contact).toBe(null)

    device.ring({ from: '+2' }).cancel()
    expect(call.state.step).toBe('idle')
  })

  it('ends on the far hang-up, keeps the card for a note, and clears on dismiss', async () => {
    const { call } = setup()
    await call.start()
    const ringing = window.__crmTelephonyMock.twilio.ring({ from: '+1' })
    call.accept()
    vi.advanceTimersByTime(3000)

    ringing.remoteHangUp()
    expect(call.state.step).toBe('ended')
    expect(call.state.seconds).toBe(3)
    expect(call.isLive()).toBe(false)

    vi.advanceTimersByTime(10_000)
    expect(call.state.seconds).toBe(3)
    call.dismiss()
    expect(call.state.step).toBe('idle')
  })

  it('turns a second caller away while one call is live', async () => {
    const { call } = setup()
    await call.start()
    const device = window.__crmTelephonyMock.twilio
    device.ring({ from: '+1' })
    const second = device.ring({ from: '+2' })

    expect(second.state).toBe('closed')
    expect(call.state.contact.number).toBe('+1')
  })
})

describe('an outgoing call', () => {
  it('rings until the far end answers, and a cancel before that closes it', async () => {
    const { call } = setup()
    await call.start()

    await call.makeCall('+15550100101')
    expect(call.state.step).toBe('ringing')
    await flush()
    const outgoing = window.__crmTelephonyMock.twilio.calls[0]
    expect(call.state.callSid).toBe('mock-tw-out-1')

    outgoing.answer()
    expect(call.state.step).toBe('oncall')

    call.hangUp()
    expect(call.state.step).toBe('ended')
  })

  it('goes idle when hung up before it was answered', async () => {
    const { call } = setup()
    await call.start()
    await call.makeCall('+15550100101')
    call.hangUp()
    expect(call.state.step).toBe('idle')
  })
})

describe('during a call', () => {
  it('toggles mute on the call', async () => {
    const { call } = setup()
    await call.start()
    window.__crmTelephonyMock.twilio.ring({ from: '+1' })
    call.accept()

    call.toggleMute()
    expect(call.state.muted).toBe(true)
    call.toggleMute()
    expect(call.state.muted).toBe(false)
  })

  it('links a note or task to the call log by the call sid, and not before it connects', async () => {
    const { api, call } = setup()
    await call.start()
    window.__crmTelephonyMock.twilio.ring({ from: '+1', callSid: 'CA1' })
    expect(call.linkToCall('FCRM Note', { name: 'N-1' })).toBeUndefined()

    call.accept()
    await call.linkToCall('FCRM Note', { name: 'N-1' })
    expect(api.link).toHaveBeenCalledWith('CA1', 'FCRM Note', 'N-1')
  })

  it('an unknown number has no record to open', async () => {
    const { call } = setup({ mobile_no: '+1' })
    await call.start()
    window.__crmTelephonyMock.twilio.ring({ from: '+1' })
    await flush()
    expect(call.state.contact).toMatchObject({ name: '', record: null })
  })
})

describe('start', () => {
  it('keeps the error and registers no device when the server gives no token', async () => {
    const api = { token: async () => ({ ok: false, detail: 'Phone number is not mapped' }) }
    const call = createTwilioCall({ api, loadDevice: async () => MockDevice })
    vi.spyOn(console, 'error').mockImplementation(() => {})

    await call.start()

    expect(call.state.error).toBe('Phone number is not mapped')
    expect(window.__crmTelephonyMock).toBeUndefined()
  })
})

describe('formatClock', () => {
  it('pads minutes and seconds', () => {
    expect(formatClock(65)).toBe('01:05')
  })
})
