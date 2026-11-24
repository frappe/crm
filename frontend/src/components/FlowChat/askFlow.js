import { call, frappeRequest } from 'frappe-ui'
import { reactive, ref } from 'vue'
import { openFlowSession } from '@/utils/brief'
import { hasFlowLauncher } from '@/utils/flowLauncher'
import { foldFlowEvent, keepEarlierTurn } from './flowEvents'

const SUBSCRIBE_TIMEOUT = 15_000
const POLL_INTERVAL = 4_000
const RECORD_ROUTES = {
  Lead: ['CRM Lead', 'leadId'],
  Deal: ['CRM Deal', 'dealId'],
  Contact: ['Contact', 'contactId'],
  Organization: ['CRM Organization', 'organizationId'],
}

// The one open chat, shared by Home and the command palette: its latest turn, and
// the answered turns before it.
export const askFlow = reactive({
  open: false,
  session: null,
  earlier: [],
  question: '',
  answer: '',
  status: 'idle', // idle | loading | working | answered | needs_you | error
  label: '',
  error: '',
  seconds: 0,
  startedAt: 0,
  replies: [],
  multiSelect: false,
  rating: null,
  approval: null, // { seq, calls, answers } while a run waits on the user
  context: null,
  useContext: true,
})

export const canAskFlow = ref(false)

const stream = {
  socket: null,
  session: null,
  cursor: 0,
  partial: '',
  echo: null,
  poll: null,
}

const EMPTY_CHAT = {
  session: null,
  earlier: [],
  question: '',
  answer: '',
  status: 'idle',
  label: '',
  error: '',
  seconds: 0,
  replies: [],
  rating: null,
  approval: null,
  context: null,
  useContext: true,
}

export function setAskFlowSocket(socket) {
  if (stream.socket === socket || !socket) return
  stream.socket = socket
  socket.on('flow:event', (event) => {
    if (event?.session_id === stream.session) onLiveEvent(event)
  })
  socket.on('flow:resync', (notice) => {
    if (notice?.session === stream.session) fetchEntries()
  })
  socket.on('connect', () => stream.session && follow(stream.session))
}

export async function loadAskFlowAvailability() {
  if (canAskFlow.value || !hasFlowLauncher()) return
  const enabled = frappeRequest({
    url: 'frappe.flow.api.is_enabled',
    method: 'GET',
  })
  canAskFlow.value = Boolean(await enabled.catch(() => false))
}

/** The record the current page shows, for Flow to read first. */
export function recordContext(route, pageTitle = '') {
  const [doctype, param] = RECORD_ROUTES[route?.name] || []
  const name = doctype && route.params?.[param]
  if (!name) return null
  const title = pageTitle.trim()
  return { doctype, name, title: title && title !== name ? title : '' }
}

export function messageWithContext(question, context) {
  if (!context) return question
  const title = context.title ? ` (${context.title})` : ''
  return `Context: I am looking at ${context.doctype} ${context.name}${title}.\n\n${question}`
}

export function showAskFlow() {
  askFlow.open = true
}

export function hideAskFlow() {
  askFlow.open = false
}

/** Clears the open chat, for a new question. */
export function newChat() {
  unfollow()
  Object.assign(askFlow, structuredClone(EMPTY_CHAT))
}

/** Opens one of the user's earlier chats, from Flow's log. */
export async function openChat(session) {
  if (session === askFlow.session) return
  newChat()
  Object.assign(askFlow, { session, status: 'loading' })
  await follow(session)
  if (askFlow.session === session && askFlow.status === 'loading')
    askFlow.status = 'idle'
}

/** The user's Flow chats, newest first, as Flow's own history lists them. */
export function listChats(query = '') {
  return call('frappe.flow.api.list_sessions', { query, limit: 20 })
}

/** Starts a new chat, or continues the shown one when `followUp` is set. */
export async function ask(question, { context = null, followUp = false } = {}) {
  const text = question.trim()
  if (!text || askFlow.status === 'working') return
  if (!followUp) resetChat(context)
  startTurn(text)
  const message = messageWithContext(
    text,
    askFlow.useContext ? askFlow.context : null,
  )
  try {
    if (followUp && askFlow.session) {
      await call('frappe.flow.api.run', { session: askFlow.session, message })
    } else {
      const { session } = await call('crm.api.home.ask_flow', { message })
      askFlow.session = session
      await follow(session)
    }
  } catch (error) {
    fail(error?.messages?.[0] || error?.message || __('Could not reach Flow'))
  }
}

export function retry() {
  const question = askFlow.question
  // the failed turn is not kept among the earlier ones
  Object.assign(askFlow, { status: 'idle', answer: '' })
  return ask(question, { followUp: Boolean(askFlow.session) })
}

/**
 * Answers one call of the waiting batch with "Approve", "Deny" or what to change, as
 * Flow's panel does. A deny stops the run, so it denies the calls still undecided. The
 * batch goes to Flow once every call has an answer.
 */
export async function answerApproval(callId, answer) {
  const approval = askFlow.approval
  if (!approval) return
  approval.answers[callId] = answer
  if (answer === 'Deny') {
    for (const call of approval.calls)
      if (!(call.id in approval.answers)) approval.answers[call.id] = 'Deny'
  }
  if (approval.calls.some((call) => !(call.id in approval.answers))) return
  await sendApproval(approval)
}

export function approveAll() {
  const approval = askFlow.approval
  if (!approval) return
  for (const call of approval.calls)
    if (!(call.id in approval.answers)) approval.answers[call.id] = 'Approve'
  return sendApproval(approval)
}

async function sendApproval(approval) {
  Object.assign(askFlow, { status: 'working', label: __('Working') })
  try {
    await call('frappe.flow.api.resume', {
      session: askFlow.session,
      answers: { ...approval.answers },
      approval_seq: approval.seq,
    })
  } catch (error) {
    // the batch reopens, as Flow's panel does after a failed resume
    approval.answers = {}
    Object.assign(askFlow, { status: 'needs_you', label: '' })
    throw error
  }
}

/** Rates the chat's latest run as Flow's own thumbs do; "None" clears the rating. */
export async function rate(rating, comment = '') {
  const { runs = [] } = await call('frappe.flow.api.session', {
    session: askFlow.session,
  })
  const run = runs.at(-1)
  if (!run) return
  const result = await call('frappe.flow.api.submit_feedback', {
    run_name: run.name,
    rating,
    comment,
  })
  askFlow.rating = result.rating || null
  return result
}

export async function stop() {
  if (askFlow.status !== 'working' || !askFlow.session) return
  await call('frappe.flow.api.abort', { session: askFlow.session }).catch(
    () => {},
  )
}

/** Hands the chat to Flow's panel, where approvals and tool screens are drawn. */
export function openInFlow() {
  if (!askFlow.session) return false
  openFlowSession(askFlow.session)
  return true
}

function resetChat(context) {
  newChat()
  askFlow.context = context
}

function startTurn(question) {
  keepEarlierTurn(askFlow)
  Object.assign(askFlow, {
    question,
    answer: '',
    status: 'working',
    label: __('Working'),
    error: '',
    seconds: 0,
    replies: [],
    rating: null,
  })
  stream.partial = ''
  stream.echo = question
}

function fail(message) {
  Object.assign(askFlow, { status: 'error', error: message, label: '' })
}

async function follow(session) {
  stream.session = session
  const subscribed = await subscribe(session)
  if (stream.session !== session) return
  await fetchEntries()
  if (!subscribed) startPolling()
}

function unfollow() {
  if (stream.session) stream.socket?.emit('flow:unsubscribe', stream.session)
  clearInterval(stream.poll)
  Object.assign(stream, { session: null, cursor: 0, echo: null, poll: null })
}

function subscribe(session) {
  if (!stream.socket?.connected) return Promise.resolve(false)
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(false), SUBSCRIBE_TIMEOUT)
    stream.socket.emit('flow:subscribe', session, (ack) => {
      clearTimeout(timer)
      resolve(ack?.subscribed === true)
    })
  })
}

// Without realtime (Vite's dev port, a refused subscribe) the log is read on a timer.
function startPolling() {
  clearInterval(stream.poll)
  stream.poll = setInterval(() => {
    if (askFlow.status === 'working') fetchEntries()
  }, POLL_INTERVAL)
}

async function fetchEntries() {
  const session = stream.session
  if (!session) return
  const data = await call('frappe.flow.api.entries', {
    session,
    since: stream.cursor,
    // a chat opened from history reads only its current branch
    path: stream.cursor ? 'all' : 'active',
  }).catch(() => null)
  if (!data || stream.session !== session) return
  for (const row of data.entries || []) applyDurable(row)
}

function onLiveEvent(event) {
  if (typeof event.seq !== 'number')
    return foldFlowEvent(askFlow, stream, event)
  if (event.seq <= stream.cursor) return
  if (event.seq > stream.cursor + 1) return fetchEntries()
  applyDurable(event)
}

function applyDurable(row) {
  if (typeof row.seq !== 'number' || row.seq <= stream.cursor) return
  stream.cursor = row.seq
  foldFlowEvent(askFlow, stream, row)
}
