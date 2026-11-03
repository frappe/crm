import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createExotelCall,
  readExotelEvent,
} from '../../../crm/fcrm/frontend/telephony/exotelCall.js'
import ringing from '../../../crm/integrations/telephony_mock/fixtures/exotel_inbound_ringing.json'
import completed from '../../../crm/integrations/telephony_mock/fixtures/exotel_inbound_completed.json'
import noAnswer from '../../../crm/integrations/telephony_mock/fixtures/exotel_inbound_no_answer.json'
import outRinging from '../../../crm/integrations/telephony_mock/fixtures/exotel_outbound_ringing.json'
import outInProgress from '../../../crm/integrations/telephony_mock/fixtures/exotel_outbound_in_progress.json'
import outCompleted from '../../../crm/integrations/telephony_mock/fixtures/exotel_outbound_completed.json'
import outNoAnswer from '../../../crm/integrations/telephony_mock/fixtures/exotel_outbound_no_answer.json'

// Exotel's published samples, marked synthetic in each fixture; the handler's own tests replay the same files.
const payload = (fixture, sid) => ({ ...fixture.payload, CallSid: sid })

function setup() {
  const handlers = {}
  const socket = {
    on: vi.fn((event, handler) => (handlers[event] = handler)),
    off: vi.fn(),
  }
  const api = {
    call: vi.fn().mockResolvedValue({ CallSid: 'X-OUT' }),
    contact: vi.fn().mockResolvedValue({
      full_name: 'Alice Johnson',
      lead: 'CRM-LEAD-1',
      name: 'C-1',
    }),
    link: vi.fn().mockResolvedValue(null),
  }
  const call = createExotelCall({ api, socket })
  call.start()
  return { api, call, socket, send: (event) => handlers.exotel_call(event) }
}

beforeEach(() =>
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] }),
)
afterEach(() => vi.useRealTimers())

describe('reading an Exotel event', () => {
  it('names the phase of each recorded payload', () => {
    const phases = [
      [ringing, 'ringing'],
      [completed, 'ended'],
      [noAnswer, 'noanswer'],
      [outRinging, 'customer'],
      [outInProgress, 'oncall'],
      [outCompleted, 'ended'],
      [outNoAnswer, 'noanswer'],
    ].map(([fixture]) => readExotelEvent(fixture.payload)?.phase)
    expect(phases).toEqual([
      'ringing',
      'ended',
      'noanswer',
      'customer',
      'oncall',
      'ended',
      'noanswer',
    ])
  })

  it('ignores an event that changes nothing', () => {
    expect(
      readExotelEvent({ Direction: 'incoming', Status: 'free' }),
    ).toBeNull()
    expect(readExotelEvent({})).toBeNull()
  })
})

describe('an incoming call', () => {
  it('rings from the recorded payload, resolves the caller, then ends with its duration', async () => {
    const { call, send } = setup()
    send(payload(ringing, 'X-IN'))
    expect(call.state.step).toBe('incoming')
    expect(call.state.callSid).toBe('X-IN')
    expect(call.isLive()).toBe(true)
    await vi.waitFor(() =>
      expect(call.state.contact.name).toBe('Alice Johnson'),
    )
    expect(call.state.contact.record).toEqual({
      doctype: 'CRM Lead',
      name: 'CRM-LEAD-1',
    })

    send(payload(completed, 'X-IN'))
    expect(call.state.step).toBe('ended')
    expect(call.state.seconds).toBe(42)
    expect(call.isLive()).toBe(false)
  })

  it('a call nobody took, or the caller cancelled, closes the window', () => {
    const { call, send } = setup()
    send(payload(ringing, 'X-IN'))
    send(payload(noAnswer, 'X-IN'))
    expect(call.state.step).toBe('idle')
    expect(call.state.contact).toBe(null)
    expect(call.isLive()).toBe(false)

    send(payload(ringing, 'X-IN'))
    expect(call.state.step).toBe('idle')
  })

  it('a repeated ring of a call that has ended does not bring it back', () => {
    const { call, send } = setup()
    send(payload(ringing, 'X-IN'))
    send(payload(completed, 'X-IN'))
    call.dismiss()
    send(payload(ringing, 'X-IN'))
    expect(call.state.step).toBe('idle')
  })

  it('a second call and the events of a call this tab does not follow change nothing', () => {
    const { call, send } = setup()
    send(payload(completed, 'X-OTHER'))
    expect(call.state.step).toBe('idle')

    send(payload(ringing, 'X-IN'))
    send(payload(ringing, 'X-SECOND'))
    expect(call.state.callSid).toBe('X-IN')
  })

  it('dismiss clears an ended call, and a live one stays', () => {
    const { call, send } = setup()
    send(payload(ringing, 'X-IN'))
    call.dismiss()
    expect(call.state.step).toBe('incoming')
    send(payload(completed, 'X-IN'))
    call.dismiss()
    expect(call.state.step).toBe('idle')
  })
})

describe('an outgoing call', () => {
  it('rings our phone, then the customer, then runs the clock, then ends', async () => {
    const { api, call, send } = setup()
    await call.makeCall('+915550100101')
    expect(api.call).toHaveBeenCalledWith('+915550100101')
    expect(call.state).toMatchObject({
      step: 'ringing',
      callSid: 'X-OUT',
      customerRinging: false,
    })

    send(payload(outRinging, 'X-OUT'))
    expect(call.state.customerRinging).toBe(true)
    send(payload(outInProgress, 'X-OUT'))
    expect(call.state.step).toBe('oncall')
    await vi.advanceTimersByTimeAsync(3000)
    expect(call.state.seconds).toBe(3)

    send(payload(outCompleted, 'X-OUT'))
    expect(call.state.step).toBe('ended')
    expect(call.state.seconds).toBe(42)
  })

  it('an event that arrives before the dial answers waits for the call sid', async () => {
    const { api, call, send } = setup()
    api.call.mockImplementation(async () => {
      send(payload(outRinging, 'X-OUT'))
      return { CallSid: 'X-OUT' }
    })
    await call.makeCall('+915550100101')
    expect(call.state.customerRinging).toBe(true)
  })

  it('a refused dial goes back to idle and says why', async () => {
    const { api, call } = setup()
    api.call.mockRejectedValue(new Error('Exotel Number Missing'))
    await expect(call.makeCall('+915550100101')).rejects.toThrow()
    expect(call.state.step).toBe('idle')
    expect(call.state.error).toBe('Exotel Number Missing')
  })

  it('clears the last dial error, so the same failure is told again', async () => {
    const { api, call } = setup()
    api.call.mockRejectedValue(new Error('Exotel Number Missing'))
    await expect(call.makeCall('+915550100101')).rejects.toThrow()
    const dial = call.makeCall('+915550100101')
    expect(call.state.error).toBe('')
    await expect(dial).rejects.toThrow()
    expect(call.state.error).toBe('Exotel Number Missing')
  })

  it('does not dial a second call while one is live', async () => {
    const { api, call } = setup()
    await call.makeCall('+915550100101')
    await call.makeCall('+915550100102')
    expect(api.call).toHaveBeenCalledTimes(1)
  })
})

describe('after a reload', () => {
  it('reopens on the live call with its clock running', () => {
    const { call } = setup()
    call.restore({
      call_sid: 'X-LIVE',
      incoming: false,
      status: 'In Progress',
      number: '+915550100101',
      seconds: 90,
    })
    expect(call.state).toMatchObject({
      step: 'oncall',
      callSid: 'X-LIVE',
      seconds: 90,
    })
  })

  it('a ringing call comes back ringing and a later event still ends it', () => {
    const { call, send } = setup()
    call.restore({
      call_sid: 'X-IN',
      incoming: true,
      status: 'Ringing',
      number: '+915550100101',
      seconds: 3,
    })
    expect(call.state.step).toBe('incoming')
    send(payload(completed, 'X-IN'))
    expect(call.state.step).toBe('ended')
  })
})

it('links a note or task to the call log, and leaves a call with no log alone', () => {
  const { api, call } = setup()
  call.linkToCall('X-IN', 'FCRM Note', { name: 'N-1' })
  expect(api.link).toHaveBeenCalledWith('X-IN', 'FCRM Note', 'N-1')
  call.linkToCall('', 'FCRM Note', { name: 'N-1' })
  expect(api.link).toHaveBeenCalledTimes(1)
})

it('stops listening when the window goes', () => {
  const { call, socket } = setup()
  call.destroy()
  expect(socket.off).toHaveBeenCalledWith('exotel_call', expect.any(Function))
})
