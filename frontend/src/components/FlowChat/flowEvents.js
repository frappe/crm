const CONTEXT_PREFIX = /^Context: I am looking at [^\n]*\n\n/

/** The question as the user typed it, without the record context the palette adds. */
export function questionText(content) {
  const text = Array.isArray(content)
    ? content
        .filter((block) => block.type === 'text')
        .map((block) => block.text)
        .join('\n')
    : String(content || '')
  return text.replace(CONTEXT_PREFIX, '').trim()
}

/**
 * Folds one Flow event into the shown chat: the latest turn's question, answer, live
 * line and status, and the answered turns before it. `turn` holds what the stream
 * tracks between events: the streaming text and the question sent but not yet logged.
 */
export function foldFlowEvent(state, turn, event) {
  switch (event.type) {
    case 'run_started':
      // a new run takes the batch it was resumed with
      Object.assign(state, {
        status: 'working',
        label: __('Working'),
        error: '',
        startedAt: event.ts || 0,
        approval: null,
      })
      break
    case 'user_message':
      startLoggedTurn(state, turn, questionText(event.content))
      break
    case 'replies_suggested':
      state.replies = event.replies || []
      state.multiSelect = Boolean(event.multi_select)
      break
    case 'text_delta':
      turn.partial += event.text || ''
      state.answer = turn.partial
      state.label = ''
      break
    case 'assistant_message':
      commitAssistantText(state, turn, event)
      break
    case 'tool_call_started':
    case 'tool_call_display_ready':
      state.label = toolLabel(event)
      break
    case 'approval_required':
      Object.assign(state, {
        status: 'needs_you',
        label: '',
        approval: { seq: event.seq, calls: event.calls || [], answers: {} },
      })
      break
    case 'tool_result':
      dropAnsweredCall(state, event.tool_call_id)
      break
    case 'run_error':
      Object.assign(state, { status: 'error', error: event.message, label: '' })
      break
    case 'run_ended':
      endRun(state, event)
      break
  }
}

/** Moves the shown turn into the earlier ones; a turn without an answer is dropped. */
export function keepEarlierTurn(state) {
  if (state.question && state.answer)
    state.earlier.push({ question: state.question, answer: state.answer })
}

// The log's copy of a message sent from here only confirms it; any other starts a turn.
function startLoggedTurn(state, turn, question) {
  if (turn.echo) {
    turn.echo = null
  } else {
    keepEarlierTurn(state)
    state.question = question
  }
  Object.assign(state, { answer: '', replies: [], rating: null })
  turn.partial = ''
}

// Only the latest message shows: narration between tool calls gives way to the answer.
function commitAssistantText(state, turn, event) {
  const text = (event.content || [])
    .filter((block) => block.type === 'text' && block.text)
    .map((block) => block.text)
    .join('\n\n')
  turn.partial = ''
  if (!text) return
  state.answer = text
  state.label = ''
}

// A call answered elsewhere (Flow's panel, a cancel) leaves the batch.
function dropAnsweredCall(state, callId) {
  if (!state.approval) return
  const calls = state.approval.calls.filter((call) => call.id !== callId)
  state.approval = calls.length ? { ...state.approval, calls } : null
}

function endRun(state, { reason, ts }) {
  state.label = ''
  if (reason !== 'paused') state.approval = null
  if (ts && state.startedAt)
    state.seconds = Math.max(1, Math.round(ts - state.startedAt))
  if (reason === 'paused') state.status = 'needs_you'
  else if (state.status !== 'error') state.status = 'answered'
}

/** What a tool call is doing, from its display template or its name. */
export function toolLabel(event) {
  const display = (event.display || []).map((segment) => segment.text).join('')
  if (display.trim()) return display.trim()
  const name = String(event.name || '').replace(/_/g, ' ')
  return name ? name[0].toUpperCase() + name.slice(1) : __('Working')
}
