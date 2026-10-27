import { createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

export const homeVersion = ref(0)

export function refreshHome() {
  homeVersion.value++
}

export function useHomeWidget(widget, config = () => ({})) {
  const resource = createResource({
    url: 'crm.api.home.get_widget',
    makeParams: () => ({ widget, doctype: config().doctype || 'Both' }),
    auto: true,
  })
  watch([homeVersion, () => config().doctype], () => resource.reload())
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
