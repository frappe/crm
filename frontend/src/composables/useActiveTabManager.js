import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

export function useActiveTabManager(tabs, storageKey) {
  const activeTab = useStorage(storageKey, 'activity')
  const route = useRoute()
  const router = useRouter()

  const changeTabTo = (tabName) => {
    let index = findTabIndex(tabName)
    if (index == -1) return
    tabIndex.value = index
  }

  const preserveLastVisitedTab = useDebounceFn((tabName) => {
    activeTab.value = tabName.toLowerCase()
  }, 300)

  function setActiveTabInUrl(tabName) {
    let hash = '#' + tabName.toLowerCase()
    if (route.hash === hash) return
    router.push({ ...route, hash })
  }

  function getActiveTabFromUrl() {
    return route.hash.replace('#', '')
  }

  function findTabIndex(tabName) {
    return tabs.value?.findIndex(
      (tabOptions) => tabOptions.name.toLowerCase() === tabName,
    )
  }

  function getTabIndex(tabName) {
    let index = findTabIndex(tabName)
    return index !== -1 ? index : 0 // Default to the first tab if not found
  }

  function getActiveTab() {
    let _activeTab = getActiveTabFromUrl()
    if (_activeTab) {
      let index = findTabIndex(_activeTab)
      if (index !== -1) {
        preserveLastVisitedTab(_activeTab)
        return index
      }
      return 0
    }

    let lastVisitedTab = activeTab.value
    if (lastVisitedTab) {
      return getTabIndex(lastVisitedTab)
    }

    return 0 // Default to the first tab if nothing is found
  }

  const tabIndex = ref(getActiveTab())

  watch(tabIndex, (tabIndexValue) => {
    let currentTab = tabs.value?.[tabIndexValue].name
    setActiveTabInUrl(currentTab)
    preserveLastVisitedTab(currentTab)
  })

  watch(
    () => route.hash,
    (tabValue) => {
      if (!tabValue) return

      let tabName = tabValue.replace('#', '')
      let index = findTabIndex(tabName)
      if (index === -1) index = 0

      let currentTab = tabs.value?.[index].name
      preserveLastVisitedTab(currentTab)
      tabIndex.value = index
    },
  )

  watch(tabs, () => {
    tabIndex.value = getActiveTab()
  })

  return { tabIndex, changeTabTo }
}
