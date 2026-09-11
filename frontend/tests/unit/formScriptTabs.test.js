import { reactive } from 'vue'
import { filterVisibleTabs, mergeFormTabs } from '@/utils/formTabs'

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
    names: filterVisibleTabs(mergeFormTabs(baseTabs, document.tabs)).map(
      (tab) => tab.name,
    ),
  }
}

describe('hiding a tab from a real form script', () => {
  it('removes the tab the script hid', async () => {
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Comments', hide: true })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Emails', 'Tasks'])
  })

  it('stays correct when onRender fires repeatedly', async () => {
    const script = `
      class CRMDeal {
        onRender() {
          this.tabs.push({ name: 'Comments', hide: true })
        }
      }
    `
    const { document, names } = await tabsAfter(script, { renders: 3 })
    // The script really did push three times...
    expect(document.tabs).toHaveLength(3)
    // ...and the tab bar is unchanged by the repeats.
    expect(names).toEqual(['Activity', 'Emails', 'Tasks'])
  })

  it('hides conditionally when hide is a function', async () => {
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Tasks', hide: () => this.doc.name === 'CRM-DEAL-0001' })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Emails', 'Comments'])
  })

  it('hides and adds in the same script', async () => {
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Emails', hide: true })
          this.tabs.push({ name: 'Excom', label: 'Excom' })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Comments', 'Tasks', 'Excom'])
  })

  it('does nothing when the script misspells the tab name', async () => {
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Comment', hide: true })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Emails', 'Comments', 'Tasks'])
  })

  it('survives a script whose hide guard throws', async () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { names } = await tabsAfter(`
      class CRMDeal {
        onLoad() {
          this.tabs.push({ name: 'Tasks', hide: () => { throw new Error('boom') } })
        }
      }
    `)
    expect(names).toEqual(['Activity', 'Emails', 'Comments', 'Tasks'])
    spy.mockRestore()
  })
})
