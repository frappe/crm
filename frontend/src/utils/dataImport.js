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

const importQueryKeys = [
  'import',
  'import_field',
  'import_user',
  'import_from',
  'import_to',
]

// "Go to list" shows only what one import touched: records its user created
// (or, for updates, changed) between making the import and its last finish.
export function importListQuery(dataImport) {
  const { name, owner, creation, modified, import_type } = dataImport
  return {
    import: name,
    import_field:
      import_type === 'Insert New Records' ? 'creation' : 'modified',
    import_user: owner,
    import_from: creation,
    import_to: modified,
  }
}

export function importListFilters(query) {
  const { import_field, import_user, import_from, import_to } = query
  if (!query.import || !import_user || !import_from || !import_to) return {}
  const range = ['between', [import_from, import_to]]
  if (import_field === 'modified') {
    return { modified_by: import_user, modified: range }
  }
  return { owner: import_user, creation: range }
}

export function withoutImportQuery(query) {
  const rest = { ...query }
  for (const key of importQueryKeys) delete rest[key]
  return rest
}
