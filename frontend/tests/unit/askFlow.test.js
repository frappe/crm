import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, nextTick } from 'vue'

const call = vi.fn(() => Promise.resolve({ session: 'S-1' }))

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    call: (...args) => call(...args),
    frappeRequest: vi.fn(),
    toast: { error: vi.fn() },
    Button: defineComponent({ setup: () => () => h('button') }),
  }
})

vi.mock('@/utils/brief', () => ({
  askFlowChips: () => [],
  openFlowSession: () => true,
}))

vi.mock('@/components/FlowChat/FlowChatCard.vue', async () => {
  const { h } = await import('vue')
  return { default: { render: () => h('section', 'answer') } }
})

vi.mock('@/components/FlowChat/ChatHistory.vue', async () => {
  const { h } = await import('vue')
  return { default: { render: () => h('span') } }
})

const { default: AskFlow } = await import('@/components/Home/AskFlow.vue')
const { askFlow, newChat } = await import('@/components/FlowChat/askFlow')

let app
let root

function mountAskFlow() {
  root = document.createElement('div')
  app = createApp(AskFlow, { resource: { data: { available: true } } })
  app.config.globalProperties.__ = (text) => text
  app.mount(root)
  return root.querySelector('textarea')
}

async function press(textarea, init) {
  textarea.value = 'Who is waiting on me?'
  textarea.dispatchEvent(new Event('input'))
  const event = new KeyboardEvent('keydown', {
    key: 'Enter',
    cancelable: true,
    ...init,
  })
  textarea.dispatchEvent(event)
  await nextTick()
  return event
}

afterEach(() => {
  app?.unmount()
  call.mockClear()
  newChat()
})

describe('Ask Flow box', () => {
  it.each([
    ['Enter', {}],
    ['Cmd+Enter', { metaKey: true }],
    ['Ctrl+Enter', { ctrlKey: true }],
  ])('sends on %s', async (_, init) => {
    const event = await press(mountAskFlow(), init)
    expect(event.defaultPrevented).toBe(true)
    expect(call).toHaveBeenCalledWith('crm.api.home.ask_flow', {
      message: 'Who is waiting on me?',
    })
  })

  it('adds a new line on Shift+Enter', async () => {
    const event = await press(mountAskFlow(), { shiftKey: true })
    expect(event.defaultPrevented).toBe(false)
    expect(call).not.toHaveBeenCalled()
  })

  it('does not send while an IME is composing', async () => {
    await press(mountAskFlow(), { isComposing: true })
    expect(call).not.toHaveBeenCalled()
  })

  it('turns into the answer for the question sent', async () => {
    const textarea = mountAskFlow()
    await press(textarea, {})
    expect(askFlow.question).toBe('Who is waiting on me?')
    expect(root.querySelector('textarea')).toBeNull()
    expect(root.querySelector('section').textContent).toBe('answer')
  })
})
