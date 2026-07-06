import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const chartTypes = ref([])

export const chartOptionsByType = ref({})

export const chartOptions = createResource({
  url: 'crm.api.dashboard.get_chart_options',
  cache: 'crm-dashboard-chart-options',
  auto: true,
  onSuccess: (data = {}) => {
    const { chart_types = [], ...optionsByType } = data
    chartTypes.value = chart_types
    chartOptionsByType.value = optionsByType
  },
})
