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

  it('keeps the remembered tab when an earlier tab is hidden', () => {
    localStorage.setItem('lastDealTab', 'comments')
    const { activeTab } = useActiveTabManager(
      visible(['Emails']),
      'lastDealTab',
    )
    expect(activeTab.value).toBe('comments')
  })

  it('falls back to the first tab when the url hash points at a hidden tab', () => {
    route.hash = '#comments'
    const { activeTab } = useActiveTabManager(
      visible(['Comments']),
      'lastDealTab',
    )
    expect(activeTab.value).toBe('activity')
  })

  it('ignores changeTabTo for a hidden tab instead of throwing', () => {
    const { activeTab, changeTabTo } = useActiveTabManager(
      visible(['Emails']),
      'lastDealTab',
    )
    changeTabTo('emails')
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
  const tabs = computed(() => [
    ...allTabs,
    { name: 'Shipping Notes', value: 'shipping-notes' },
    { name: 'عروض', value: 'عروض' },
  ])

  it('selects a slugified tab from the url hash', () => {
    route.hash = '#shipping-notes'
    const { activeTab } = useActiveTabManager(tabs, 'lastDealTab')
    expect(activeTab.value).toBe('shipping-notes')
  })

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
  const none = () => computed(() => [])

  it('does not throw while resolving the active tab', () => {
    localStorage.setItem('lastDealTab', 'comments')
    expect(() => useActiveTabManager(none(), 'lastDealTab')).not.toThrow()
  })

  it('does not throw when the active tab changes', async () => {
    const { activeTab } = useActiveTabManager(none(), 'lastDealTab')
    activeTab.value = 'emails'
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
