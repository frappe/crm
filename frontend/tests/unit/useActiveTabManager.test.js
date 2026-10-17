import { computed, nextTick, reactive } from 'vue'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const route = reactive({ hash: '' })
const push = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push }),
}))

beforeEach(() => {
  route.hash = ''
  push.mockClear()
  localStorage.clear()
})

describe('useActiveTabManager with every tab hidden', () => {
  it('does not throw or navigate', async () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { activeTab } = useActiveTabManager(
      computed(() => []),
      'lastDealTab',
    )
    activeTab.value = 'emails'
    route.hash = '#emails'
    await expect(nextTick()).resolves.not.toThrow()
    expect(push).not.toHaveBeenCalled()
  })
})
