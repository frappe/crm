import { createResource } from 'frappe-ui'
import { ref } from 'vue'
import { globalStore } from '@/stores/global'

const isDemoDataCreated = ref(window.demo_data_created || false)

const _clearDemoData = createResource({
  url: 'crm.demo.api.clear_demo_data',
  onSuccess() {
    isDemoDataCreated.value = false
    window.location.reload()
  },
})

export function useDemoData() {
  const { $dialog } = globalStore()

  const clearDemoData = () => {
    $dialog({
      title: __('Clear Demo Data'),
      message: __(
        'Are you sure you want to clear demo data? This action cannot be undone.',
      ),
      actions: [
        {
          label: __('Confirm'),
          theme: 'red',
          variant: 'solid',
          onClick: (close) => {
            _clearDemoData.submit()
            close()
          },
        },
      ],
    })
  }

  return {
    isDemoDataCreated,
    clearDemoData,
  }
}
