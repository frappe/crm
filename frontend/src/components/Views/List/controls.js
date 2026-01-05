import { useViews } from '@/stores/view'
import { call } from 'frappe-ui'
import { inject } from 'vue'
import { useRoute } from 'vue-router'

export function useControls() {
  const doctype = inject('doctype')
  const route = useRoute()
  const { currentView } = useViews(doctype)

  function createOrUpdateStandardView() {
    if (route.query.view) return

    currentView.value.doctype = doctype
    currentView.value.route_name = route.name

    call(
      'crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_standard_view',
      { view: currentView.value },
    )
  }

  function updateFilter() {
    createOrUpdateStandardView()
  }

  function updateSort() {
    createOrUpdateStandardView()
  }

  function updateColumns() {
    createOrUpdateStandardView()
  }

  return {
    updateFilter,
    updateSort,
    updateColumns,
    createOrUpdateStandardView,
  }
}
