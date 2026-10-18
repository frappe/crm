import { createApp, h, ref } from 'vue'

vi.mock('frappe-ui', () => ({ Dropdown: { render: () => null } }))
vi.mock('@/stores/global', () => ({
  globalStore: () => ({ makeCall: vi.fn() }),
}))
vi.mock('@/composables/whatsapp', () => ({ whatsappEnabled: ref(false) }))
vi.mock('@/composables/telephony', () => ({ callEnabled: ref(false) }))

const { default: ActivityHeader } =
  await import('@/components/Activities/ActivityHeader.vue')

function headingFor(props) {
  const root = document.createElement('div')
  const app = createApp({
    render: () => h(ActivityHeader, { customPane: true, ...props }),
  })
  app.config.globalProperties.__ = __
  app.config.warnHandler = () => {}
  app.mount(root)
  const text = root.querySelector('.text-2xl-semibold')?.textContent.trim()
  app.unmount()
  return text
}

describe('ActivityHeader heading', () => {
  it('shows the tab label when a script relabels a built-in tab', () => {
    expect(headingFor({ title: 'Emails', label: 'Inbox' })).toBe('Inbox')
  })

  it('falls back to the tab name without a label', () => {
    expect(headingFor({ title: 'Emails' })).toBe('Emails')
  })
})
