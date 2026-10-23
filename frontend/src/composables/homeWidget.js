import { createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

// Bumped after a row action so every widget and the header counts reload together.
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
