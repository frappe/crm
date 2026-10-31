import { afterEach, describe, expect, it, vi } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'

const runMethod = vi.fn()

vi.mock('@framework/ui/api', () => ({ runMethod }))
vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')
  const stub = (name, render) =>
    defineComponent({
      name,
      props: ['label', 'theme', 'message'],
      setup: (props) => () => render(props),
    })
  return {
    Badge: stub('Badge', (props) =>
      h('span', { 'data-badge': props.theme }, props.label),
    ),
    ErrorMessage: stub('ErrorMessage', (props) =>
      h('p', { 'data-error': '' }, props.message),
    ),
    Skeleton: stub('Skeleton', () => h('span', { 'data-skeleton': '' })),
  }
})

const { default: EmailAccounts } = await import(
  '../../../crm/fcrm/frontend/settings/email-accounts.vue'
)

let app
let root

async function mountBlock() {
  root = document.createElement('div')
  app = createApp(
    defineComponent(() => () => h(EmailAccounts, { bindings: {} })),
  )
  app.mount(root)
  await new Promise((resolve) => setTimeout(resolve))
  await nextTick()
  return root
}

afterEach(() => {
  app?.unmount()
  runMethod.mockReset()
})

describe('email-accounts settings block', () => {
  it('reads the session user own accounts with a GET', async () => {
    runMethod.mockResolvedValue({ data: [] })

    await mountBlock()

    expect(runMethod).toHaveBeenCalledWith(
      'frappe.email.inbox.get_own_email_accounts',
      {},
      { http: 'GET' },
    )
  })

  it('lists each account with its address, read-only', async () => {
    runMethod.mockResolvedValue({
      data: [
        {
          email_account: 'Sales',
          email_id: 'sales@example.com',
          enable_outgoing: 1,
          awaiting_password: 0,
        },
        {
          email_account: 'Support',
          email_id: 'help@example.com',
          enable_outgoing: 0,
          awaiting_password: 1,
        },
      ],
    })

    const block = await mountBlock()
    const rows = [...block.querySelectorAll('[data-email-account]')]

    expect(rows.map((row) => row.dataset.emailAccount)).toEqual([
      'Sales',
      'Support',
    ])
    expect(rows[0].textContent).toContain('sales@example.com')
    expect(badges(rows[0])).toEqual(['Outgoing'])
    expect(badges(rows[1])).toEqual(['Awaiting password'])
    expect(block.querySelector('button, input')).toBeNull()
  })

  it('says so when no account is linked', async () => {
    runMethod.mockResolvedValue({ data: [] })

    const block = await mountBlock()

    expect(block.textContent).toContain(
      'No email account is linked to you yet.',
    )
  })

  it('shows an error when the read fails', async () => {
    runMethod.mockRejectedValue(new Error('boom'))

    const block = await mountBlock()

    expect(block.querySelector('[data-error]').textContent).toBe(
      'Email accounts could not load: boom',
    )
  })
})

function badges(row) {
  return [...row.querySelectorAll('[data-badge]')].map(
    (badge) => badge.textContent,
  )
}
