import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

export function useActiveTabManager(tabs, storageKey) {
  const activieTab = useStorage(storageKey, 'activity')
  const route = useRoute()

  const preserveLastVisitedTab = useDebounceFn((tabName) => {
    activieTab.value = tabName.toLowerCase()
  }, 300)

  function setActiveTabInUrl(tabName) {
    window.location.hash = '#' + tabName.toLowerCase()
  }

  function getActiveTabFromUrl() {
    return route.hash.replace('#', '')
  }

  function findTabIndex(tabName) {
    return tabs.value.findIndex(
      (tabOptions) => tabOptions.name.toLowerCase() === tabName,
    )
  }

  function getTabIndex(tabName) {
    let index = findTabIndex(tabName)
    return index !== -1 ? index : 0 // Default to the first tab if not found
  }

  function getActiveTabFromLocalStorage() {
    return activieTab.value
  }

  function getActiveTab() {
    let activeTab = getActiveTabFromUrl()
    if (activeTab) {
      let index = findTabIndex(activeTab)
      if (index !== -1) {
        preserveLastVisitedTab(activeTab)
        return index
      }
      return 0
    }

    let lastVisitedTab = getActiveTabFromLocalStorage()
    if (lastVisitedTab) {
      return getTabIndex(lastVisitedTab)
    }

    return 0 // Default to the first tab if nothing is found
  }

  const tabIndex = ref(getActiveTab())

  watch(tabIndex, (tabIndexValue) => {
    let currentTab = tabs.value[tabIndexValue].name
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

      let currentTab = tabs.value[index].name
      preserveLastVisitedTab(currentTab)
      tabIndex.value = index
    },
  )

  return { tabIndex }
}
