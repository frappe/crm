import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const call = vi.fn()

vi.mock('frappe-ui', () => ({
  call: (...args) => call(...args),
  frappeRequest: vi.fn(),
}))

const {
  ask,
  askFlow,
  rate,
  canAskFlow,
  messageWithContext,
  recordContext,
  newChat,
  openChat,
} = await import('@/components/FlowChat/askFlow')
const { foldFlowEvent, questionText, toolLabel } =
  await import('@/components/FlowChat/flowEvents')
const { askFlowCommands } =
  await import('@/components/CommandPalette/askFlowCommands')
const { groupCommands } = await import('@/utils/commandPalette')
const { isPlainClick, linkRecordNames } =
  await import('@/components/FlowChat/flowAnswer')

function freshTurn() {
  const state = {
    earlier: [],
    question: '',
    answer: '',
    status: 'working',
    label: '',
    error: '',
  }
  return { state, turn: { partial: '', echo: null } }
}

function fold(events) {
  const { state, turn } = freshTurn()
  for (const event of events) foldFlowEvent(state, turn, event)
  return state
}

describe('foldFlowEvent', () => {
  it('streams text, then keeps the durable message in its place', () => {
    const { state, turn } = freshTurn()
    foldFlowEvent(state, turn, { type: 'text_delta', text: 'Three ' })
    foldFlowEvent(state, turn, { type: 'text_delta', text: 'deals' })
    expect(state.answer).toBe('Three deals')
    foldFlowEvent(state, turn, {
      type: 'assistant_message',
      content: [
        { type: 'thinking', thinking: 'hidden' },
        { type: 'text', text: 'Three deals stalled.' },
      ],
    })
    expect(state.answer).toBe('Three deals stalled.')
  })

  it('shows only the latest message, so narration gives way to the answer', () => {
    const state = fold([
      {
        type: 'assistant_message',
        content: [{ type: 'text', text: 'Let me check the deals.' }],
      },
      { type: 'assistant_message', content: [] },
      { type: 'text_delta', text: 'Two' },
    ])
    expect(state.answer).toBe('Two')
  })

  it('starts a new answer for each user message', () => {
    const state = fold([
      { type: 'assistant_message', content: [{ type: 'text', text: 'Old' }] },
      { type: 'user_message', content: 'next' },
    ])
    expect(state.answer).toBe('')
  })

  it('shows the running tool as the live line', () => {
    const state = fold([
      {
        type: 'tool_call_display_ready',
        name: 'read_records',
        display: [{ text: 'Reading ' }, { text: 'CRM Deal', arg: 'doctype' }],
      },
    ])
    expect(state.label).toBe('Reading CRM Deal')
  })

  it('asks for the user on an approval or a paused run', () => {
    expect(fold([{ type: 'approval_required', calls: [] }]).status).toBe(
      'needs_you',
    )
    expect(fold([{ type: 'run_ended', reason: 'paused' }]).status).toBe(
      'needs_you',
    )
  })

  it('keeps a run error after the run ends', () => {
    const state = fold([
      { type: 'run_error', message: 'Provider timed out' },
      { type: 'run_ended', reason: 'error' },
    ])
    expect(state).toMatchObject({
      status: 'error',
      error: 'Provider timed out',
    })
  })

  it('times the run from its own start and end', () => {
    const state = fold([
      { type: 'run_started', ts: 100.2 },
      { type: 'run_ended', reason: 'done', ts: 134.6 },
    ])
    expect(state.seconds).toBe(34)
  })

  it('offers the replies Flow suggests until the next message', () => {
    const state = fold([
      { type: 'replies_suggested', replies: ['Show me the deals.'] },
    ])
    expect(state.replies).toEqual(['Show me the deals.'])
    foldFlowEvent(state, { partial: '', echo: null }, { type: 'user_message' })
    expect(state.replies).toEqual([])
  })

  it('marks a finished run answered', () => {
    expect(fold([{ type: 'run_ended', reason: 'done' }]).status).toBe(
      'answered',
    )
  })
})

describe('earlier turns', () => {
  const answer = (text) => ({
    type: 'assistant_message',
    content: [{ type: 'text', text }],
  })

  it('keeps answered turns before the latest when a chat is replayed', () => {
    const state = fold([
      { type: 'user_message', content: 'How many deals?' },
      answer('There are 11 deals.'),
      { type: 'user_message', content: 'Show me the deals' },
      answer('Here they are.'),
    ])
    expect(state.earlier).toEqual([
      { question: 'How many deals?', answer: 'There are 11 deals.' },
    ])
    expect(state).toMatchObject({
      question: 'Show me the deals',
      answer: 'Here they are.',
    })
  })

  it('takes the log copy of a message sent from here as a confirmation', () => {
    const { state, turn } = freshTurn()
    Object.assign(state, { question: 'Count deals' })
    turn.echo = 'Count deals'
    foldFlowEvent(state, turn, { type: 'user_message', content: 'Count deals' })
    expect(state.earlier).toEqual([])
    expect(turn.echo).toBeNull()
  })

  it('drops a turn that never got an answer', () => {
    const state = fold([
      { type: 'user_message', content: 'First' },
      { type: 'run_error', message: 'Timed out' },
      { type: 'user_message', content: 'Second' },
    ])
    expect(state.earlier).toEqual([])
  })
})

describe('questionText', () => {
  it('leaves out the record context the palette adds', () => {
    expect(
      questionText(
        'Context: I am looking at CRM Deal CRM-DEAL-2026-00003 (Acme).\n\nWho is the contact?',
      ),
    ).toBe('Who is the contact?')
  })
})

describe('toolLabel', () => {
  it('falls back to the tool name', () => {
    expect(toolLabel({ name: 'find_doctypes' })).toBe('Find doctypes')
  })
})

describe('recordContext', () => {
  it('names the record a record page shows', () => {
    const route = { name: 'Deal', params: { dealId: 'CRM-DEAL-2026-00008' } }
    expect(recordContext(route, 'Northwind Traders')).toEqual({
      doctype: 'CRM Deal',
      name: 'CRM-DEAL-2026-00008',
      title: 'Northwind Traders',
    })
  })

  it('drops a page title that only repeats the name', () => {
    const route = { name: 'Organization', params: { organizationId: 'Acme' } }
    expect(recordContext(route, 'Acme').title).toBe('')
  })

  it('is empty on other pages', () => {
    expect(recordContext({ name: 'Deals', params: {} })).toBeNull()
  })
})

describe('messageWithContext', () => {
  it('puts the record before the question', () => {
    const context = {
      doctype: 'CRM Lead',
      name: 'CRM-LEAD-2026-00001',
      title: 'Asha Rao',
    }
    expect(messageWithContext('Who is this?', context)).toBe(
      'Context: I am looking at CRM Lead CRM-LEAD-2026-00001 (Asha Rao).\n\nWho is this?',
    )
    expect(messageWithContext('Hi', null)).toBe('Hi')
  })
})

describe('linkRecordNames', () => {
  it('links bare and code-quoted deal and lead names', () => {
    expect(
      linkRecordNames('See CRM-DEAL-2026-00008 and `CRM-LEAD-2026-00012`.'),
    ).toBe(
      'See [CRM-DEAL-2026-00008](/crm/deals/CRM-DEAL-2026-00008) and [CRM-LEAD-2026-00012](/crm/leads/CRM-LEAD-2026-00012).',
    )
  })

  it('leaves names that are already links alone', () => {
    const text = '[CRM-DEAL-2026-00008](/crm/deals/CRM-DEAL-2026-00008)'
    expect(linkRecordNames(text)).toBe(text)
  })
})

describe('askFlowCommands', () => {
  beforeEach(() => {
    canAskFlow.value = true
    Object.assign(askFlow, { session: null, question: '', status: 'idle' })
  })

  it('offers nothing to users who cannot use Flow', () => {
    canAskFlow.value = false
    expect(askFlowCommands('stalled deals', {})).toEqual([])
  })

  it('offers to ask from three characters, keeping the palette open', () => {
    expect(askFlowCommands('hi', {})).toEqual([])
    const [command] = askFlowCommands('stalled deals', {})
    expect(command).toMatchObject({
      id: 'ask-flow',
      title: 'Ask Flow: stalled deals',
      keepOpen: true,
    })
  })

  it('ranks the ask row after matches, and first when nothing matches', () => {
    const [ask] = askFlowCommands('deals', {})
    const deals = { id: 'deals', title: 'Deals', group: 'Navigate' }
    const withMatch = groupCommands([ask, deals], 'deals').flatMap(
      (g) => g.items,
    )
    expect(withMatch.map((c) => c.id)).toEqual(['deals', 'ask-flow'])
    const alone = groupCommands([ask, deals], 'which deals stalled')
    expect(alone.flatMap((g) => g.items)[0].id).toBe('ask-flow')
  })
})

describe('ask', () => {
  afterEach(() => call.mockReset())

  it('starts a chat with the page record and reads its log', async () => {
    call.mockImplementation((method) =>
      method === 'crm.api.home.ask_flow'
        ? Promise.resolve({ session: 'S-2' })
        : Promise.resolve({
            entries: [
              { seq: 1, type: 'run_started' },
              {
                seq: 2,
                type: 'assistant_message',
                content: [{ type: 'text', text: 'Two open deals.' }],
              },
              { seq: 3, type: 'run_ended', reason: 'done' },
            ],
          }),
    )
    Object.assign(askFlow, { status: 'idle' })
    const context = {
      doctype: 'CRM Deal',
      name: 'CRM-DEAL-2026-00008',
      title: '',
    }
    await ask('How many open deals?', { context })
    expect(call).toHaveBeenCalledWith('crm.api.home.ask_flow', {
      message:
        'Context: I am looking at CRM Deal CRM-DEAL-2026-00008.\n\nHow many open deals?',
    })
    expect(call).toHaveBeenCalledWith('frappe.flow.api.entries', {
      session: 'S-2',
      since: 0,
      path: 'active',
    })
    expect(askFlow).toMatchObject({
      session: 'S-2',
      status: 'answered',
      answer: 'Two open deals.',
    })
  })
})

describe('rate', () => {
  afterEach(() => call.mockReset())

  it('rates the latest run of the chat', async () => {
    call.mockImplementation((method) =>
      method === 'frappe.flow.api.session'
        ? Promise.resolve({ runs: [{ name: 'R-1' }, { name: 'R-2' }] })
        : Promise.resolve({ rating: 'Up' }),
    )
    askFlow.session = 'S-3'
    await rate('Up')
    expect(call).toHaveBeenLastCalledWith('frappe.flow.api.submit_feedback', {
      run_name: 'R-2',
      rating: 'Up',
      comment: '',
    })
    expect(askFlow.rating).toBe('Up')
  })
})

describe('isPlainClick', () => {
  const click = (keys = {}) => ({ button: 0, ...keys })

  it('leaves Cmd, Ctrl, Shift and middle clicks to the browser', () => {
    expect(isPlainClick(click())).toBe(true)
    expect(isPlainClick(click({ metaKey: true }))).toBe(false)
    expect(isPlainClick(click({ ctrlKey: true }))).toBe(false)
    expect(isPlainClick(click({ shiftKey: true }))).toBe(false)
    expect(isPlainClick(click({ button: 1 }))).toBe(false)
  })
})

describe('openChat and newChat', () => {
  afterEach(() => call.mockReset())

  it('opens an earlier chat from its log, then clears it for a new one', async () => {
    call.mockResolvedValue({
      entries: [
        { seq: 1, type: 'run_started', ts: 10 },
        { seq: 2, type: 'user_message', content: 'Count deals' },
        {
          seq: 3,
          type: 'assistant_message',
          content: [{ type: 'text', text: 'There are 11 deals.' }],
        },
        { seq: 4, type: 'run_ended', reason: 'done', ts: 15 },
      ],
    })
    await openChat('S-OLD')
    expect(call).toHaveBeenCalledWith('frappe.flow.api.entries', {
      session: 'S-OLD',
      since: 0,
      path: 'active',
    })
    expect(askFlow).toMatchObject({
      session: 'S-OLD',
      question: 'Count deals',
      answer: 'There are 11 deals.',
      status: 'answered',
      seconds: 5,
    })
    newChat()
    expect(askFlow).toMatchObject({
      session: null,
      question: '',
      answer: '',
      earlier: [],
      status: 'idle',
    })
  })
})
