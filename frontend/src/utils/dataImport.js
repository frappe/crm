import { timestampCell } from '@/composables/useTimelinePreferences'

const statusColorMap = {
  Pending: 'gray',
  'In Progress': 'blue',
  Success: 'green',
  'Partial Success': 'amber',
  Error: 'red',
  'Timed Out': 'amber',
}

export function getDataImportRow(row, dataImport) {
  if (row === 'status') {
    return {
      label: dataImport.status,
      color: statusColorMap[dataImport.status] || 'gray',
    }
  }
  if (row === 'reference_doctype') return __(dataImport.reference_doctype)
  if (row === 'import_file') {
    if (dataImport.import_file) return dataImport.import_file.split('/').pop()
    return dataImport.google_sheets_url || ''
  }
  if (['modified', 'creation'].includes(row)) {
    return timestampCell(dataImport[row])
  }
  return dataImport[row]
}
