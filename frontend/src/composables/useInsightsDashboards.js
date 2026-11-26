import { getSettings } from '@/stores/settings'
import { computed } from 'vue'

export const SHIPPED_DASHBOARD = Object.freeze({
  dashboard: 'crm',
  label: 'CRM',
  is_default: 1,
})

export function useInsightsDashboards() {
  const { _settings: settings } = getSettings()

  const rows = computed(() => {
    const saved = settings.doc?.insights_dashboards
    return saved?.length ? saved : [SHIPPED_DASHBOARD]
  })

  // the shipped dashboard shows until the table is saved, so seed it before the first edit
  function editableRows() {
    if (!settings.doc.insights_dashboards?.length) {
      settings.doc.insights_dashboards = [{ ...SHIPPED_DASHBOARD }]
    }
    return settings.doc.insights_dashboards
  }

  return { settings, rows, editableRows }
}
