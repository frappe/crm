import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick, onMounted, ref } from 'vue'

const call = vi.hoisted(() => vi.fn())

vi.mock('frappe-ui', async () => {
  const { defineComponent } = await import('vue')
  const stub = defineComponent({ setup: () => () => null })
  return {
    call,
    createResource: () => ({ data: '' }),
    toast: { promise: vi.fn(), error: vi.fn(), success: vi.fn() },
    dayjsLocal: vi.fn(),
    Badge: stub,
    Dropdown: stub,
  }
})

vi.mock('@framework/ui/telemetry', () => ({
  useTelemetry: () => ({ capture: vi.fn() }),
}))

vi.mock('@/components/Activities/TimelineTimestamp.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/Activities/EmailContent.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/components/AttachmentItem.vue', () => ({
  default: { render: () => null },
}))
vi.mock('@/utils/dialogs', () => ({ createDialog: vi.fn() }))
vi.mock('@/utils', () => ({
  isContentEmpty: (html) => !html,
  htmlToText: (html) => html,
}))
vi.mock('@/composables/emailSubject', () => ({
  getEmailSubject: () => 'Your CRM trial',
  loadUserEmailSubjects: vi.fn(),
}))
vi.mock('@/stores/users', () => ({
  usersStore: () => ({
    getUser: () => ({ email: 'jane@example.com', full_name: 'Jane' }),
  }),
}))
vi.mock('@/components/CommentBox.vue', () => ({
  default: { render: () => null },
}))

// Composer state only; the real editor needs tiptap and a session
vi.mock('@/components/EmailEditor.vue', async () => {
  const { defineComponent, h, ref } = await import('vue')
  const chain = new Proxy({}, { get: (_, key) => () => key === 'run' || chain })
  const editor = {
    commands: { focus: () => {}, setContent: () => {} },
    getHTML: () => '',
    chain: () => chain,
    state: { doc: { forEach: () => {} } },
  }
  return {
    default: defineComponent({
      props: { submitButtonProps: Object, discardButtonProps: Object },
      emits: ['update:content'],
      setup(props, { emit, expose }) {
        expose({
          editor,
          subject: ref(''),
          fromEmail: ref(''),
          replyAddresses: ref([]),
          toEmails: ref(['lead@example.com']),
          ccEmails: ref([]),
          bccEmails: ref([]),
          cc: ref(false),
          bcc: ref(false),
          inReplyTo: ref(''),
          sendBlocked: ref(false),
          write: (html) => emit('update:content', html),
        })
        return () =>
          h('div', [
            h('button', { onClick: props.submitButtonProps.onClick }, 'Send'),
            h(
              'button',
              { onClick: props.discardButtonProps.onClick },
              'Discard',
            ),
          ])
      },
    }),
  }
})

const { default: CommunicationArea } = await import(
  '@/components/CommunicationArea.vue'
)
const { default: EmailArea } = await import(
  '@/components/Activities/EmailArea.vue'
)

// Registered globally in the app, so the components do not import it
const Button = defineComponent({
  props: { tooltip: String, label: String },
  setup:
    (props, { attrs }) =>
    () =>
      h('button', { onClick: attrs.onClick }, props.tooltip || props.label),
})

const receivedEmail = {
  name: 'COMM-0001',
  data: {
    subject: 'Your CRM trial',
    sender: 'lead@example.com',
    recipients: 'jane@example.com',
    content: '<p>Can we see a demo?</p>',
  },
}

let root, app, emailBox

function mountTimeline() {
  root = document.createElement('div')
  document.body.appendChild(root)
  app = createApp(
    defineComponent({
      setup() {
        const box = ref(null)
        const ready = ref(false)
        onMounted(() => {
          emailBox = box.value
          ready.value = true
        })
        return () => [
          h(CommunicationArea, {
            ref: box,
            modelValue: { name: 'CRM-LEAD-0001', email: 'lead@example.com' },
          }),
          ready.value &&
            h(EmailArea, { activity: receivedEmail, emailBox: box.value }),
        ]
      },
    }),
  )
  app.component('Button', Button)
  app.config.globalProperties.__ = __
  app.config.warnHandler = () => {}
  app.mount(root)
  return nextTick()
}

// The activity renders after the composer, so its Reply is the last one
function click(label) {
  const buttons = [...root.querySelectorAll('button')]
  buttons.findLast((b) => b.textContent === label).click()
}

async function send(html) {
  emailBox.editor.write(html)
  await nextTick()
  click('Send')
  await vi.waitFor(() => expect(call).toHaveBeenCalled())
  const [, payload] = call.mock.calls.at(-1)
  await nextTick()
  return payload
}

describe('Email reply threading', () => {
  beforeEach(async () => {
    localStorage.clear()
    call.mockReset().mockResolvedValue({})
    await mountTimeline()
  })

  afterEach(() => {
    app.unmount()
    root.remove()
  })

  it('sends a reply with the email it replies to as in_reply_to', async () => {
    click('Reply')
    const payload = await send('<p>Sure, tomorrow?</p>')

    expect(payload.subject).toBe('Re: Your CRM trial')
    expect(payload.in_reply_to).toBe('COMM-0001')
  })

  it('does not thread the next new email on a sent reply', async () => {
    click('Reply')
    await send('<p>Sure, tomorrow?</p>')
    call.mockClear()

    const payload = await send('<p>New topic</p>')

    expect(payload.in_reply_to).toBeUndefined()
  })

  it('drops the reply target when the reply is discarded', async () => {
    click('Reply')
    await nextTick()
    click('Discard')
    await vi.waitFor(() => expect(emailBox.editor.inReplyTo).toBe(''))
  })

  it('keeps the reply target of a restored scheduled reply', async () => {
    emailBox.restoreDraft({
      subject: 'Re: Your CRM trial',
      recipients: 'lead@example.com',
      content: '<p>Following up</p>',
      sender: 'jane@example.com',
      attachments: [],
      in_reply_to: 'COMM-0001',
    })
    await nextTick()
    click('Send')
    await vi.waitFor(() => expect(call).toHaveBeenCalled())

    expect(call.mock.calls.at(-1)[1].in_reply_to).toBe('COMM-0001')
  })
})
