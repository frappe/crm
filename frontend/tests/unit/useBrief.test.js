import { beforeEach, describe, expect, it, vi } from 'vitest'

const flushPromises = () => new Promise((resolve) => setTimeout(resolve))

const replies = {}
const call = vi.fn((method, params) => {
  if (method === 'crm.api.home.get_brief') {
    const tab = params.tab || replies.saved
    return Promise.resolve({ tab, total: replies[tab], items: [] })
  }
  if (method === 'crm.api.home.get_brief_count') {
    return Promise.resolve(replies[params.tab])
  }
  return Promise.resolve()
})

vi.mock('frappe-ui', () => ({
  call: (...args) => call(...args),
  toast: { error: vi.fn() },
}))
vi.mock('@/stores/users', () => ({
  usersStore: () => ({ isManager: () => true }),
}))

const { refreshHome, useBrief } = await import('@/composables/homeWidget')

function briefCalls() {
  return call.mock.calls.filter(
    ([method]) => method === 'crm.api.home.get_brief',
  )
}

beforeEach(() => {
  call.mockClear()
  Object.assign(replies, { saved: 'team', team: 26, mine: 3 })
})

describe('useBrief', () => {
  it('opens on the tab the server saved', async () => {
    const { tab, brief, counts } = useBrief()
    expect(tab.value).toBe(null)
    await flushPromises()
    expect(briefCalls()[0][1]).toEqual({})
    expect(tab.value).toBe('team')
    expect(brief.value.total).toBe(26)
    expect(counts.value).toEqual({ team: 26, mine: 3 })
  })

  it('saves the tab the user switches to', async () => {
    const { setTab } = useBrief()
    await flushPromises()
    setTab('mine')
    expect(call).toHaveBeenCalledWith('crm.api.home.set_brief_tab', {
      tab: 'mine',
    })
  })

  it('shows a tab seen before at once while it reloads', async () => {
    const { brief, setTab } = useBrief()
    await flushPromises()
    setTab('mine')
    await flushPromises()
    setTab('team')
    expect(brief.value.tab).toBe('team')
    expect(briefCalls().at(-1)[1]).toEqual({ tab: 'team' })
  })

  it('ignores a reply that a doctype change made stale', async () => {
    const { brief, setDoctype } = useBrief()
    await flushPromises()
    let answerStale
    call.mockImplementationOnce(
      () => new Promise((resolve) => (answerStale = resolve)),
    )
    refreshHome()
    setDoctype('Deal')
    await flushPromises()
    answerStale({ tab: 'team', total: 99, items: [] })
    await flushPromises()
    expect(brief.value.total).toBe(26)
  })
})
