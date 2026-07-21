import type { Ref } from 'vue'

interface ColumnWidthPayload {
  key: string
  width: string
  save: boolean
}

interface ListColumn {
  key: string
  width?: string | number
  [key: string]: unknown
}

interface ListResource {
  data?: { columns?: ListColumn[] }
}

/**
 * frappe-ui v1's ListHeaderItem emits the new width on resize instead of
 * mutating the column itself, so the consumer has to apply it. This returns a
 * handler that writes the width into `list.data.columns` (driving the header
 * grid's live repaint) and bubbles the debounced save (`save: true`) upstream
 * so the view gets persisted.
 */
export function createColumnResizeHandler(
  list: Ref<ListResource | undefined>,
  emit: (event: 'columnWidthUpdated', ...args: unknown[]) => void,
) {
  return function onColumnWidthUpdated(payload?: ColumnWidthPayload) {
    if (!payload) return
    const { key, width, save } = payload
    const column = list.value?.data?.columns?.find((c) => c.key === key)
    if (column) column.width = width
    if (save) emit('columnWidthUpdated')
  }
}
