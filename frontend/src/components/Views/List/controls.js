import { useCall } from 'frappe-ui'
import { useList } from './list.js'
import { inject } from 'vue'
import { useRoute } from 'vue-router'

export function useControls() {
  const doctype = inject('doctype')
  const currentView = inject('currentView')
  const { reload } = useList()

  const route = useRoute()

  function createOrUpdateStandardView() {
    if (route.query.view) return

    currentView.value.doctype = doctype
    currentView.value.route_name = route.name

    useCall({
      url: '/api/v2/method/crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_standard_view',
      method: 'POST',
      params: { view: currentView.value },
      onSuccess: () => reload(),
    })
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

  function applyRowItemFilter({ event, idx, column, item, firstColumn }) {
    let restrictedFieldtypes = ['Duration', 'Datetime', 'Time']
    if (restrictedFieldtypes.includes(column.type) || idx === 0) return
    if (idx === 1 && firstColumn.key == '_liked_by') return

    event.stopPropagation()
    event.preventDefault()

    let filters = currentView.value?.filters || {}

    let value = item.name || item.label || item

    if (value) {
      filters[column.key] = value
    } else {
      delete filters[column.key]
    }

    if (column.key == '_assign') {
      if (item.length > 1) {
        let target = event.target.closest('.user-avatar')
        if (target) {
          let name = target.getAttribute('data-name')
          filters['_assign'] = ['LIKE', `%${name}%`]
        }
      } else {
        filters['_assign'] = ['LIKE', `%${item[0].name}%`]
      }
    }
    updateFilter()
  }

  return {
    applyRowItemFilter,
    updateFilter,
    updateSort,
    updateColumns,
    createOrUpdateStandardView,
  }
}
