import { nextTick, ref } from 'vue'

const { call, toast, createResource } = vi.hoisted(() => {
  const toast = vi.fn()
  toast.success = vi.fn()
  toast.error = vi.fn()
  return {
    call: vi.fn(),
    toast,
    createResource: vi.fn((options) => ({ data: null, options })),
  }
})

vi.mock('frappe-ui', () => ({ call, toast, createResource }))

import { useContactTabs } from '@/composables/useContactTabs'

beforeEach(() => vi.clearAllMocks())

const TABS = [{ name: 'orders', label: 'Orders' }]

function setup(activeTab = ref('orders')) {
  const composable = useContactTabs('CONT-001', activeTab)
  // run the resource success handler as frappe-ui would after the fetch
  createResource.mock.calls[0][0].onSuccess(TABS)
  return { ...composable, activeTab }
}

describe('useContactTabs', () => {
  it('loads rows for the active tab', async () => {
    call.mockResolvedValue({ rows: [{ name: 'SO-1' }], total_count: 1 })
    const { states } = setup()
    await vi.waitFor(() => expect(states.orders.rows).toHaveLength(1))
    expect(states.orders.totalCount).toBe(1)
  })

  it('empties the tab and toasts once when the provider fails', async () => {
    call.mockRejectedValue(new Error('boom'))
    const { states } = setup()
    await vi.waitFor(() => expect(states.orders.failed).toBe(true))
    expect(states.orders.rows).toEqual([])
    expect(states.orders.totalCount).toBe(0)
    expect(toast.error).toHaveBeenCalledTimes(1)
  })

  it('retries a failed tab when it is reopened', async () => {
    call.mockRejectedValueOnce(new Error('boom'))
    const activeTab = ref('orders')
    const { states } = setup(activeTab)
    await vi.waitFor(() => expect(states.orders.failed).toBe(true))

    call.mockResolvedValue({ rows: [{ name: 'SO-1' }], total_count: 1 })
    activeTab.value = 'activity'
    await nextTick()
    activeTab.value = 'orders'
    await nextTick()

    await vi.waitFor(() => expect(states.orders.rows).toHaveLength(1))
    expect(states.orders.failed).toBe(false)
    expect(states.orders.totalCount).toBe(1)
  })

  it('does not reload a tab that already loaded fine', async () => {
    call.mockResolvedValue({ rows: [], total_count: 0 })
    const activeTab = ref('orders')
    setup(activeTab)
    await vi.waitFor(() => expect(call).toHaveBeenCalledTimes(1))

    activeTab.value = 'activity'
    await nextTick()
    activeTab.value = 'orders'
    await nextTick()

    expect(call).toHaveBeenCalledTimes(1)
  })
})
