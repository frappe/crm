import { useCall } from 'frappe-ui'
import { useList } from './list.js'
import { useView } from '@/stores/view'
import { inject, reactive } from 'vue'
import { useRoute } from 'vue-router'

export const viewUpdated = reactive({})

export function useControls() {
  const doctype = inject('doctype')
  const viewName = inject('viewName')

  const { currentView, reloadCurrentView } = useView(doctype, viewName)
  const { reload } = useList()
  const route = useRoute()

  const createOrUpdateViewCall = useCall({
    url: '/api/v2/method/crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_view',
    method: 'POST',
    immediate: false,
    onSuccess: () => reload(),
  })

  function createOrUpdateView() {
    currentView.value.doctype = doctype
    currentView.value.route_name = route.name

    if (!createOrUpdateViewCall.isFetching) {
      createOrUpdateViewCall.submit({ view: currentView.value })
    }

    viewUpdated[viewName] = false
  }

  function updateFilter() {
    if (viewName) {
      viewUpdated[viewName] = true
    } else {
      createOrUpdateView()
    }
  }

  function updateSort() {
    if (viewName) {
      viewUpdated[viewName] = true
    } else {
      createOrUpdateView()
    }
  }

  function updateColumns() {
    if (viewName) {
      viewUpdated[viewName] = true
    } else {
      createOrUpdateView()
    }
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

  function saveView() {
    createOrUpdateView()
  }

  function cancelChanges() {
    viewUpdated[viewName] = false
    reloadCurrentView()
  }

  return {
    applyRowItemFilter,
    updateFilter,
    updateSort,
    updateColumns,
    createOrUpdateView,
    saveView,
    cancelChanges,
  }
}
