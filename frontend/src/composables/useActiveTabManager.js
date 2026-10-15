import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

export function useActiveTabManager(tabs, storageKey) {
  const lastVisitedTab = useStorage(storageKey, 'activity')
  const route = useRoute()
  const router = useRouter()

  const changeTabTo = (tabName) => {
    if (!hasTab(tabName)) return
    activeTab.value = tabName
  }

  const preserveLastVisitedTab = useDebounceFn((tabName) => {
    lastVisitedTab.value = tabName
  }, 300)

  function setActiveTabInUrl(tabName) {
    let hash = '#' + tabName
    if (route.hash === hash) return
    router.push({ ...route, hash })
  }

  function getActiveTabFromUrl() {
    return route.hash.replace('#', '')
  }

  function hasTab(tabName) {
    return tabs.value?.some((tab) => tab.value === tabName)
  }

  function firstTab() {
    return tabs.value?.[0]?.value
  }

  function getActiveTab() {
    let _activeTab = getActiveTabFromUrl()
    if (_activeTab) {
      if (hasTab(_activeTab)) {
        preserveLastVisitedTab(_activeTab)
        return _activeTab
      }
      return firstTab()
    }

    if (hasTab(lastVisitedTab.value)) return lastVisitedTab.value

    return firstTab()
  }

  const activeTab = ref(getActiveTab())

  watch(activeTab, (tabName) => {
    setActiveTabInUrl(tabName)
    preserveLastVisitedTab(tabName)
  })

  watch(
    () => route.hash,
    (tabValue) => {
      if (!tabValue) return

      let tabName = tabValue.replace('#', '')
      if (!hasTab(tabName)) tabName = firstTab()

      preserveLastVisitedTab(tabName)
      activeTab.value = tabName
    },
  )

  watch(tabs, () => {
    activeTab.value = getActiveTab()
  })

  return { activeTab, changeTabTo }
}
