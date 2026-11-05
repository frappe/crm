import { usersStore } from '@/stores/users'
import { createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

export const homeVersion = ref(0)

export function refreshHome() {
  homeVersion.value++
}

export function useHomeWidget(widget, config = () => ({})) {
  const resource = createResource({
    url: 'crm.api.home.get_widget',
    makeParams: () => ({
      widget,
      doctype: config().doctype || 'Both',
      period: config().period,
    }),
    auto: true,
  })
  watch([homeVersion, () => config().doctype, () => config().period], () =>
    resource.reload(),
  )
  return resource
}

export function useTabbedHomeWidget(widget, tab, config = () => ({})) {
  const resource = createResource({
    url: 'crm.api.home.get_tab',
    makeParams: () => ({
      widget,
      tab: tab.value,
      doctype: config().doctype || 'Both',
    }),
    auto: true,
  })
  watch([homeVersion, tab, () => config().doctype], () => resource.reload())
  return resource
}

export function useBrief() {
  const { isManager } = usersStore()
  const tab = ref(isManager() ? 'team' : 'mine')
  const showAll = ref(false)
  const resource = createResource({
    url: 'crm.api.home.get_brief',
    makeParams: () => ({ tab: tab.value, show_all: showAll.value ? 1 : 0 }),
    auto: true,
  })
  watch(tab, () => (showAll.value = false))
  watch([homeVersion, tab, showAll], () => resource.reload())
  return { tab, showAll, resource }
}
