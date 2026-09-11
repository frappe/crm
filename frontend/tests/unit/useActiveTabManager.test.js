import { computed, nextTick, reactive, ref } from 'vue'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const route = reactive({ hash: '' })
const push = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push }),
}))

const allTabs = [
  { name: 'Activity' },
  { name: 'Emails' },
  { name: 'Comments' },
]

function visible(hiddenNames = []) {
  return computed(() =>
    allTabs.filter((tab) => !hiddenNames.includes(tab.name)),
  )
}

beforeEach(() => {
  route.hash = ''
  push.mockClear()
  localStorage.clear()
})

describe('useActiveTabManager with hidden tabs', () => {
  it('selects the remembered tab while it is still visible', () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { tabIndex } = useActiveTabManager(visible(), 'lastDealTab')
    expect(tabIndex.value).toBe(2)
  })

  it('falls back to the first tab when the remembered tab is hidden', () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { tabIndex } = useActiveTabManager(visible(['Comments']), 'lastDealTab')
    expect(tabIndex.value).toBe(0)
  })

  it('re-indexes the remembered tab when an earlier tab is hidden', () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { tabIndex } = useActiveTabManager(visible(['Emails']), 'lastDealTab')
    expect(tabIndex.value).toBe(1)
  })

  it('falls back to the first tab when the url hash points at a hidden tab', () => {
    route.hash = '#comments'
    const { tabIndex } = useActiveTabManager(visible(['Comments']), 'lastDealTab')
    expect(tabIndex.value).toBe(0)
  })

  it('ignores changeTabTo for a hidden tab instead of throwing', () => {
    const { tabIndex, changeTabTo } = useActiveTabManager(
      visible(['Emails']),
      'lastDealTab',
    )
    changeTabTo('emails')
    expect(tabIndex.value).toBe(0)
  })

  it('re-resolves when the open tab is hidden while it is showing', async () => {
    const hidden = ref([])
    const tabs = computed(() =>
      allTabs.filter((tab) => !hidden.value.includes(tab.name)),
    )
    const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastDealTab')
    changeTabTo('comments')
    expect(tabIndex.value).toBe(2)

    hidden.value = ['Comments']
    await nextTick()
    expect(tabIndex.value).toBe(0)
  })
})

describe('useActiveTabManager with every tab hidden', () => {
  const none = () => computed(() => [])

  it('does not throw while resolving the active tab', () => {
    localStorage.setItem('lastDealTab', 'comments')
    expect(() => useActiveTabManager(none(), 'lastDealTab')).not.toThrow()
  })

  it('does not throw when the tab index changes', async () => {
    const { tabIndex } = useActiveTabManager(none(), 'lastDealTab')
    tabIndex.value = 1
    await expect(nextTick()).resolves.not.toThrow()
    expect(push).not.toHaveBeenCalled()
  })

  it('does not throw when the url hash changes', async () => {
    const tabs = none()
    useActiveTabManager(tabs, 'lastDealTab')
    route.hash = '#emails'
    await expect(nextTick()).resolves.not.toThrow()
  })
})
