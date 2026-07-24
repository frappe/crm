import { createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

export const chartTypes = ref([])

export const chartOptionsByType = ref({})

let errorNotified = false

export const chartOptions = createResource({
  url: 'crm.api.dashboard.get_chart_options',
  cache: 'crm-dashboard-chart-options',
  auto: true,
  onSuccess: (data = {}) => {
    const { chart_types = [], ...optionsByType } = data
    chartTypes.value = chart_types
    chartOptionsByType.value = optionsByType
    errorNotified = false
  },
  onError: () => {
    if (!errorNotified) {
      errorNotified = true
      toast.error(__('Could not load chart options'))
    }
    if (!chartTypes.value.length) {
      chartTypes.value = [{ label: __('Spacer'), value: 'spacer' }]
    }
  },
})
