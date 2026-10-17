import { reactive } from 'vue'
import { mergeFormTabs } from '@/utils/formTabs'

let listResourceOptions = null

vi.mock('frappe-ui', () => ({
  createListResource: (options) => {
    listResourceOptions = options
    return {
      loading: false,
      list: { promise: Promise.resolve() },
      fetch: vi.fn(),
    }
  },
  call: vi.fn(),
  toast: { error: vi.fn() },
}))

vi.mock('@/stores/global', () => ({
  globalStore: () => ({ $dialog: vi.fn(), $socket: {} }),
}))

vi.mock('@/stores/meta', () => ({
  getMeta: () => ({ doctypesMeta: {} }),
}))

vi.mock('@/router', () => ({ default: { push: vi.fn() } }))

vi.mock('@/utils/renderFieldLayoutDialog', () => ({
  renderFieldLayoutDialog: vi.fn(),
}))

const { getScript } = await import('@/data/script')

// The tabs a Deal page declares before any script runs.
const baseTabs = [
  { name: 'Activity', label: 'Activity' },
  { name: 'Emails', label: 'Emails' },
  { name: 'Comments', label: 'Comments' },
  { name: 'Tasks', label: 'Tasks' },
]

/**
 * Run `script` the way a CRM Form Script record runs on a Deal form, and
 * return the tab names the page would end up rendering.
 */
async function tabsAfter(script, { renders = 1 } = {}) {
  const document = reactive({ doc: { name: 'CRM-DEAL-0001' } })
  const { setupScript } = getScript('CRM Deal')

  listResourceOptions.onSuccess([
    { name: 'test-script', dt: 'CRM Deal', view: 'Form', script },
  ])

  // document.js builds the controllers and then fires the lifecycle hooks;
  // this mirrors that for the two hooks a tab script would use.
  const controllers = (await setupScript(document, {})) || []
  for (const controller of controllers) {
    await controller.onLoad?.()
    for (let i = 0; i < renders; i++) await controller.onRender?.()
  }

  return {
    document,
    names: mergeFormTabs(baseTabs, document.tabs)
      .filter((tab) => (tab.condition ? tab.condition() : true))
      .map((tab) => tab.name),
  }
}

describe('tabs from a real form script', () => {
  it('hides a built-in tab with a condition', async () => {
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Tasks', condition: () => this.doc.name !== 'CRM-DEAL-0001' })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Emails', 'Comments'])
  })

  it('stays correct when onRender pushes repeatedly', async () => {
    const script = `
      class CRMDeal {
        onRender() {
          this.tabs.push({ name: 'Comments', condition: () => false })
          this.tabs.push({ name: 'Excom', component: { render: () => h('div') } })
        }
      }
    `
    const { document, names } = await tabsAfter(script, { renders: 3 })
    expect(document.tabs).toHaveLength(6)
    expect(names).toEqual(['Activity', 'Emails', 'Tasks', 'Excom'])
  })
})
