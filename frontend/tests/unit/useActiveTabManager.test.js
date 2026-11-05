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

describe('useActiveTabManager with a note link', () => {
  const tabs = computed(() => [{ value: 'activity' }, { value: 'notes' }])

  it('opens the notes tab and keeps the note in the url', async () => {
    route.hash = '#notes/gbp2a9uafp'
    const { activeTab } = useActiveTabManager(tabs, 'lastDealTab')
    await nextTick()
    expect(activeTab.value).toBe('notes')
    expect(push).not.toHaveBeenCalled()
  })

  it('switches to the notes tab when the link opens on the same page', async () => {
    const { activeTab } = useActiveTabManager(tabs, 'lastDealTab')
    route.hash = '#notes/gbp2a9uafp'
    await nextTick()
    await nextTick()
    expect(activeTab.value).toBe('notes')
    expect(push).not.toHaveBeenCalled()
  })
})
