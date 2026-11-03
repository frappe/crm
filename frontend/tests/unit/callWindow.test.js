import { createApp, h, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CallWindow from '../../../crm/fcrm/frontend/telephony/CallWindow.vue'
import { startOutgoingCall } from '../../../crm/fcrm/frontend/telephony/callState.js'
import { callState } from '../../../crm/fcrm/frontend/telephony/callState.js'
import { MockDevice } from '../../../crm/fcrm/frontend/telephony/mockTwilioDevice.js'

vi.mock('../../../crm/fcrm/frontend/telephony/callApi.js', () => ({
  callApi: {
    token: vi.fn().mockResolvedValue({ token: 't', mock: true }),
    contact: vi.fn().mockResolvedValue({
      full_name: 'Alice Johnson',
      lead: 'CRM-LEAD-1',
      name: 'C-1',
    }),
    link: vi.fn().mockResolvedValue(null),
    exotelCall: vi.fn().mockResolvedValue({ CallSid: 'X-OUT' }),
    rememberMedium: vi.fn().mockResolvedValue(null),
  },
}))
// frappe-ui's source cannot load in node; these three stand for its Avatar, Button and Tooltip.
vi.mock('frappe-ui', async () => {
  const { h } = await import('vue')
  return {
    Avatar: {
      props: ['label'],
      render() {
        return h('div', this.label)
      },
    },
    Button: {
      props: ['label'],
      emits: ['click'],
      render() {
        return h('button', {
          'aria-label': this.label,
          onClick: () => this.$emit('click'),
        })
      },
    },
    Checkbox: {
      props: ['label', 'modelValue'],
      emits: ['update:modelValue'],
      render() {
        return h('input', {
          type: 'checkbox',
          'aria-label': this.label,
          onChange: (e) => this.$emit('update:modelValue', e.target.checked),
        })
      },
    },
    Tooltip: {
      render() {
        return h('span', this.$slots.default())
      },
    },
  }
})
vi.mock('@twilio/voice-sdk', () => ({ Device: class {} }))

const settle = async () => {
  for (let i = 0; i < 5; i++)
    await new Promise((resolve) => setTimeout(resolve, 0))
}
let root
let app
let handle
let shell

beforeEach(async () => {
  Object.assign(callState, {
    media: ['Twilio'],
    defaultMedium: null,
    liveExotel: null,
  })
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
  handle = reactive({
    state: 'closed',
    title: '',
    actions: [],
    closable: true,
    keepAlive: false,
    attention: false,
    open() {
      this.state = 'open'
    },
    minimise() {
      this.state = 'minimised'
    },
    close() {
      this.state = 'closed'
    },
    setTitle(t) {
      this.title = t
    },
    setActions(a) {
      this.actions = a
    },
    setClosable(c) {
      this.closable = c
    },
    setKeepAlive(on) {
      this.keepAlive = on
    },
    setAttention(on) {
      this.attention = on
    },
  })
  shell = {
    create: vi.fn(),
    toast: { error: vi.fn() },
    router: { push: vi.fn() },
  }
  root = document.createElement('div')
  document.body.append(root)
  await mountWindow()
})
async function mountWindow() {
  app?.unmount()
  app = createApp({ render: () => h(CallWindow, { shell, window: handle }) })
  app.mount(root)
  await settle()
}
afterEach(() => {
  vi.clearAllMocks()
  app.unmount()
  app = null
  delete globalThis.__testSocket
  root.remove()
  vi.useRealTimers()
  delete window.__crmTelephonyMock
})

const ring = async () => {
  window.__crmTelephonyMock.twilio.ring({
    from: '+15550100101',
    callSid: 'CA1',
  })
  await settle()
}
const buttons = () =>
  [...root.querySelectorAll('button')].map(
    (b) => b.getAttribute('aria-label') || b.textContent.trim()
  )
const press = async (label) => {
  root.querySelector(`button[aria-label="${label}"]`).click()
  await settle()
}

describe('the call window', () => {
  it('draws nothing and stays closed while there is no call', () => {
    expect(root.textContent.trim()).toBe('')
    expect(handle.state).toBe('closed')
    expect(handle.keepAlive).toBe(false)
  })

  it('opens on an incoming call: the frame title is the state, Accept and Reject are the buttons', async () => {
    await ring()
    expect(handle.state).toBe('open')
    expect(handle.title).toBe('Incoming call')
    expect(handle.keepAlive).toBe(true)
    expect(handle.closable).toBe(false)
    expect(root.textContent).toContain('Alice Johnson')
    expect(buttons()).toEqual(['Accept', 'Reject'])
  })

  it('pulses the pill while a caller waits, and stops once the call is answered or rejected', async () => {
    await ring()
    expect(handle.attention).toBe(true)

    await press('Accept')
    expect(handle.attention).toBe(false)
  })

  it('stops pulsing when the caller is rejected', async () => {
    await ring()
    await press('Reject')
    expect(handle.attention).toBe(false)
  })

  it('on a call it shows the timer, Mute, Note, Task, Lead and Hang up, and mute swaps its icon label', async () => {
    await ring()
    await press('Accept')
    expect(handle.title).toBe('On call')
    expect(buttons()).toEqual(['Mute', 'Note', 'Task', 'Lead', 'Hang up'])
    expect(root.textContent).toContain('00:00')

    await press('Mute')
    expect(buttons()[0]).toBe('Unmute')
  })

  it('the pill reads "name · status" and carries Mute and Hang up as its actions', async () => {
    await ring()
    await press('Accept')
    handle.minimise()
    await settle()
    expect(handle.title).toMatch(/^Alice Johnson · \d\d:\d\d$/)
    expect(handle.actions.map((a) => a.label)).toEqual(['Mute', 'Hang up'])
  })

  it('after the call it says Call ended, keeps Note, Task and Lead, and the frame can close', async () => {
    await ring()
    await press('Accept')
    await press('Hang up')
    expect(handle.title).toBe('Call ended')
    expect(handle.closable).toBe(true)
    expect(handle.keepAlive).toBe(false)
    expect(buttons()).toEqual(['Note', 'Task', 'Lead'])

    handle.close()
    await settle()
    expect(root.textContent.trim()).toBe('')
  })

  it('Note opens Quick Entry with the lead and links the saved note to the call log', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    shell.create.mockResolvedValue({ name: 'N-1' })
    await ring()
    await press('Accept')
    await press('Note')

    expect(shell.create).toHaveBeenCalledWith('FCRM Note', {
      values: {
        reference_doctype: 'CRM Lead',
        reference_docname: 'CRM-LEAD-1',
      },
    })
    expect(callApi.link).toHaveBeenCalledWith('CA1', 'FCRM Note', 'N-1')
  })

  it('a rejected call closes the window', async () => {
    await ring()
    await press('Reject')
    expect(handle.state).toBe('closed')
  })

  it('an outgoing call opens the window as Calling…, with Cancel', async () => {
    await window.__crmTelephonyMock.makeCall('+15550100101')
    await settle()
    expect(handle.title).toBe('Calling…')
    expect(buttons()).toEqual(['Cancel'])
  })
})

describe('the call window with Exotel', () => {
  let sendEvent
  const exotelWindow = async (state = {}) => {
    const handlers = {}
    globalThis.__testSocket = {
      on: (event, handler) => (handlers[event] = handler),
      off: vi.fn(),
    }
    sendEvent = (payload) => handlers.exotel_call(payload)
    Object.assign(callState, { media: ['Exotel'], ...state })
    await mountWindow()
  }
  const inbound = {
    Direction: 'incoming',
    CallSid: 'X-IN',
    CallFrom: '+15550100101',
  }

  it('rings from the user-scoped event: no call controls, only Note, Task and the lead', async () => {
    await exotelWindow()
    sendEvent({ ...inbound, EventType: 'Dial', Status: 'busy' })
    await settle()
    expect(handle.state).toBe('open')
    expect(handle.title).toBe('Incoming call')
    expect(handle.closable).toBe(false)
    expect(root.textContent).toContain('Alice Johnson')
    expect(buttons()).toEqual(['Note', 'Task', 'Lead'])
  })

  it('after the call it says Call ended and the frame can close', async () => {
    await exotelWindow()
    sendEvent({ ...inbound, EventType: 'Dial', Status: 'busy' })
    sendEvent({
      ...inbound,
      CallType: 'completed',
      DialCallStatus: 'completed',
      DialCallDuration: '42',
    })
    await settle()
    expect(handle.title).toBe('Call ended')
    expect(handle.closable).toBe(true)
    expect(root.textContent).toContain('00:42')
  })

  it('links a note made during the call to the Exotel call log', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    shell.create.mockResolvedValue({ name: 'N-9' })
    await exotelWindow()
    sendEvent({ ...inbound, EventType: 'Dial', Status: 'busy' })
    await settle()
    await press('Note')
    expect(callApi.link).toHaveBeenCalledWith('X-IN', 'FCRM Note', 'N-9')
  })

  it('reopens on the live call after a reload', async () => {
    await exotelWindow({
      liveExotel: {
        call_sid: 'X-L',
        incoming: false,
        status: 'In Progress',
        number: '+15550100101',
        seconds: 75,
      },
    })
    expect(handle.state).toBe('open')
    expect(handle.title).toBe('On call')
    expect(root.textContent).toContain('01:15')
    expect(handle.keepAlive).toBe(true)
  })

  it('an outgoing call with one medium dials at once: Ringing your phone…', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    await exotelWindow()
    await startOutgoingCall('+15550100101')
    await settle()
    expect(callApi.exotelCall).toHaveBeenCalledWith('+15550100101')
    expect(handle.title).toBe('Ringing your phone…')
    expect(buttons()).toEqual([])
  })
})

describe('the medium picker', () => {
  const both = async (defaultMedium = null) => {
    globalThis.__testSocket = { on() {}, off() {} }
    Object.assign(callState, { media: ['Twilio', 'Exotel'], defaultMedium })
    await mountWindow()
  }

  it('opens as the first step with one button per medium when there is no default', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    await both()
    startOutgoingCall('+15550100101')
    await settle()
    expect(handle.state).toBe('open')
    expect(handle.title).toBe('Call +15550100101')
    expect(handle.closable).toBe(true)
    expect(buttons()).toEqual(['Twilio', 'Exotel'])
    expect(callApi.exotelCall).not.toHaveBeenCalled()

    await press('Exotel')
    expect(callApi.exotelCall).toHaveBeenCalledWith('+15550100101')
    expect(callApi.rememberMedium).not.toHaveBeenCalled()
  })

  it('remembers the choice when asked', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    await both()
    startOutgoingCall('+15550100101')
    await settle()
    const check = root.querySelector('input[type=checkbox]')
    check.checked = true
    check.dispatchEvent(new Event('change'))
    await press('Exotel')
    expect(callApi.rememberMedium).toHaveBeenCalledWith('Exotel')
    expect(callState.defaultMedium).toBe('Exotel')
  })

  it('skips the picker for a default medium', async () => {
    const { callApi } = await import(
      '../../../crm/fcrm/frontend/telephony/callApi.js'
    )
    await both('Exotel')
    startOutgoingCall('+15550100101')
    await settle()
    expect(callApi.exotelCall).toHaveBeenCalledWith('+15550100101')
    expect(buttons()).toEqual([])
  })

  it('closing the frame drops the pending number', async () => {
    await both()
    startOutgoingCall('+15550100101')
    await settle()
    handle.close()
    await settle()
    expect(root.textContent.trim()).toBe('')
  })
})
