import { call, createResource } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

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
      columns: config().columns,
    }),
    auto: true,
  })
  const columnKeys = () =>
    config()
      .columns?.map((column) => column.key)
      .join()
  watch([homeVersion, () => config().doctype, columnKeys], () =>
    resource.reload(),
  )
  return resource
}

const widgetColumns = reactive({})
const requests = new Map()

// Fields a widget can add as columns, per doctype setting; fetched once a page load.
export function getWidgetColumns(widget, doctype = 'Both') {
  return widgetColumns[`${widget}:${doctype}`]
}

export function loadWidgetColumns(widget, doctype = 'Both') {
  const key = `${widget}:${doctype}`
  if (!requests.has(key)) {
    const request = call('crm.api.home.get_widget_columns', { widget, doctype })
      .then(({ fields, locked }) => {
        widgetColumns[key] = {
          fields: Object.fromEntries(fields.map((f) => [f.fieldname, f])),
          locked,
        }
        return widgetColumns[key]
      })
      .catch((error) => {
        requests.delete(key)
        throw error
      })
    requests.set(key, request)
  }
  return requests.get(key)
}
