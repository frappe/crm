import { computed, nextTick, reactive, ref } from 'vue'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const route = reactive({ hash: '' })
const push = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push }),
}))

const allTabs = [
  { name: 'Activity', value: 'activity' },
  { name: 'Emails', value: 'emails' },
  { name: 'Comments', value: 'comments' },
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
    const { activeTab } = useActiveTabManager(visible(), 'lastDealTab')
    expect(activeTab.value).toBe('comments')
  })

  it('falls back to the first tab when the remembered tab is hidden', () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { activeTab } = useActiveTabManager(
      visible(['Comments']),
      'lastDealTab',
    )
    expect(activeTab.value).toBe('activity')
  })

  it('falls back to the first tab when the url hash points at a hidden tab', () => {
    route.hash = '#comments'
    const { activeTab } = useActiveTabManager(
      visible(['Comments']),
      'lastDealTab',
    )
    expect(activeTab.value).toBe('activity')
  })

  it('re-resolves when the open tab is hidden while it is showing', async () => {
    const hidden = ref([])
    const tabs = computed(() =>
      allTabs.filter((tab) => !hidden.value.includes(tab.name)),
    )
    const { activeTab, changeTabTo } = useActiveTabManager(tabs, 'lastDealTab')
    changeTabTo('comments')
    expect(activeTab.value).toBe('comments')

    hidden.value = ['Comments']
    await nextTick()
    expect(activeTab.value).toBe('activity')
  })
})

describe('useActiveTabManager with script tab values', () => {
  const tabs = computed(() => [...allTabs, { name: 'عروض', value: 'عروض' }])

  it('decodes a percent-encoded hash', () => {
    route.hash = '#' + encodeURIComponent('عروض')
    const { activeTab } = useActiveTabManager(tabs, 'lastDealTab')
    expect(activeTab.value).toBe('عروض')
  })

  it('falls back to the first tab on a malformed hash', () => {
    route.hash = '#%E0%A4%A'
    const { activeTab } = useActiveTabManager(tabs, 'lastDealTab')
    expect(activeTab.value).toBe('activity')
  })
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
