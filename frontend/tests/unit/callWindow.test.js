import { createApp, h, nextTick, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CallWindow from '../../../crm/fcrm/frontend/telephony/CallWindow.vue'
import { MockDevice } from '../../../crm/fcrm/frontend/telephony/mockTwilioDevice.js'

vi.mock('../../../crm/fcrm/frontend/telephony/callApi.js', () => ({
  callApi: {
    token: vi.fn().mockResolvedValue({ token: 't', mock: true }),
    contact: vi.fn().mockResolvedValue({ full_name: 'Alice Johnson', lead: 'CRM-LEAD-1', name: 'C-1' }),
    link: vi.fn().mockResolvedValue(null),
  },
}))
// frappe-ui's source cannot load in node; these three stand for its Avatar, Button and Tooltip.
vi.mock('frappe-ui', async () => {
  const { h } = await import('vue')
  return {
    Avatar: { props: ['label'], render() { return h('div', this.label) } },
    Button: {
      props: ['label'],
      emits: ['click'],
      render() { return h('button', { 'aria-label': this.label, onClick: () => this.$emit('click') }) },
    },
    Tooltip: { render() { return h('span', this.$slots.default()) } },
  }
})
vi.mock('@twilio/voice-sdk', () => ({ Device: class {} }))

const settle = async () => {
  for (let i = 0; i < 5; i++) await new Promise((resolve) => setTimeout(resolve, 0))
}
let root
let handle
let shell

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'Date'] })
  handle = reactive({
    state: 'closed',
    title: '',
    actions: [],
    closable: true,
    keepAlive: false,
    open() { this.state = 'open' },
    minimise() { this.state = 'minimised' },
    close() { this.state = 'closed' },
    setTitle(t) { this.title = t },
    setActions(a) { this.actions = a },
    setClosable(c) { this.closable = c },
    setKeepAlive(on) { this.keepAlive = on },
  })
  shell = { create: vi.fn(), toast: { error: vi.fn() }, router: { push: vi.fn() } }
  root = document.createElement('div')
  document.body.append(root)
  createApp({ render: () => h(CallWindow, { shell, window: handle }) }).mount(root)
  await settle()
})
afterEach(() => {
  root.remove()
  vi.useRealTimers()
  delete window.__crmTelephonyMock
})

const ring = async () => {
  window.__crmTelephonyMock.twilio.ring({ from: '+15550100101', callSid: 'CA1' })
  await settle()
}
const buttons = () => [...root.querySelectorAll('button')].map((b) => b.getAttribute('aria-label') || b.textContent.trim())
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
    const { callApi } = await import('../../../crm/fcrm/frontend/telephony/callApi.js')
    shell.create.mockResolvedValue({ name: 'N-1' })
    await ring()
    await press('Accept')
    await press('Note')

    expect(shell.create).toHaveBeenCalledWith('FCRM Note', {
      values: { reference_doctype: 'CRM Lead', reference_docname: 'CRM-LEAD-1' },
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
