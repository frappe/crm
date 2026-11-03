import { afterEach, describe, expect, it, vi } from 'vitest'
import { MockDevice } from '../../../crm/fcrm/frontend/telephony/mockTwilioDevice.js'
import { loadTwilioDevice } from '../../../crm/fcrm/frontend/telephony/twilioDevice.js'

afterEach(() => {
  delete window.__crmTelephonyMock
})

describe('loadTwilioDevice', () => {
  it('returns the fake Device and never loads the SDK when the server says mock', async () => {
    const loadVoiceSdk = vi.fn()

    const Device = await loadTwilioDevice(
      { token: 't', mock: true },
      loadVoiceSdk,
    )

    expect(Device).toBe(MockDevice)
    expect(loadVoiceSdk).not.toHaveBeenCalled()
  })

  it("returns the SDK's Device for a real token", async () => {
    class Device {}
    const loadVoiceSdk = vi.fn().mockResolvedValue({ Device })

    expect(await loadTwilioDevice({ token: 't' }, loadVoiceSdk)).toBe(Device)
  })
})

describe('MockDevice', () => {
  it('registers and tells listeners', async () => {
    const device = new MockDevice('t', {})
    const registered = vi.fn()
    device.on('registered', registered)

    await device.register()

    expect(registered).toHaveBeenCalledOnce()
  })

  it('rings an incoming call whose parameters are what the call UI reads', () => {
    const device = new MockDevice('t', {})
    const incoming = vi.fn()
    device.on('incoming', incoming)

    const call = device.ring({ from: '+15550100177' })

    expect(incoming).toHaveBeenCalledWith(call)
    expect(call.parameters.From).toBe('+15550100177')
    expect(call.parameters.CallSid).toMatch(/^mock-tw-in-/)
  })

  it('accepts, mutes and disconnects a call with the SDK events', () => {
    const call = new MockDevice('t', {}).ring()
    const events = []
    for (const name of ['accept', 'mute', 'disconnect'])
      call.on(name, () => events.push(name))

    call.accept()
    call.mute()
    const mutedAfterMute = call.isMuted()
    call.mute(false)
    call.disconnect()

    expect(events).toEqual(['accept', 'mute', 'mute', 'disconnect'])
    expect([mutedAfterMute, call.isMuted()]).toEqual([true, false])
  })

  it('emits reject and cancel', () => {
    const call = new MockDevice('t', {}).ring()
    const reject = vi.fn()
    const cancel = vi.fn()
    call.on('reject', reject).on('cancel', cancel)

    call.reject()
    call.cancel()

    expect(reject).toHaveBeenCalledOnce()
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('connects an outgoing call that accepts, then answers on the test’s cue', async () => {
    const device = new MockDevice('t', {})
    const call = await device.connect({ params: { To: '+15550100177' } })
    const accept = vi.fn()
    const status = vi.fn()
    call.on('accept', accept).on('messageReceived', status)

    await new Promise((resolve) => setTimeout(resolve))
    call.answer()

    expect(accept).toHaveBeenCalledOnce()
    expect(call.parameters.To).toBe('+15550100177')
    expect(status).toHaveBeenCalledWith({
      content: { CallStatus: 'in-progress' },
    })
  })

  it('exposes the newest device to a walk on window', () => {
    const device = new MockDevice('t', {})

    expect(window.__crmTelephonyMock.twilio).toBe(device)
  })

  it('stops a listener that was taken off', () => {
    const call = new MockDevice('t', {}).ring()
    const listener = vi.fn()
    call.on('disconnect', listener)
    call.off('disconnect', listener)

    call.disconnect()

    expect(listener).not.toHaveBeenCalled()
  })
})
