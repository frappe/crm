import { globalStore } from '@/stores/global'

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
            // TODO: Use API to clear demo data
            close()
          },
        },
      ],
    })
  }

  return {
    clearDemoData,
  }
}
