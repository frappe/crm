import { timestampCell } from '@/composables/useTimelinePreferences'
import type { DataImportDoc } from '@framework/ui/components/DataImport'

export interface ListColumn {
  key: string
  label?: string
  type?: string
  align?: string
  width?: string
}

export interface DataImportList {
  data?: {
    data: DataImportRow[]
    rows: string[]
    columns: ListColumn[]
    view_type: string
    page_length_count: number
    row_count: number
    total_count: number
  }
  params?: { filters?: Record<string, unknown> }
}

export interface DataImportRow {
  status?: string
  reference_doctype?: string
  import_file?: string | null
  google_sheets_url?: string | null
  [field: string]: unknown
}

export type ImportListQuery = {
  import?: string
  import_field?: string
  import_user?: string
  import_from?: string
  import_to?: string
}

const statusColorMap: Record<string, string> = {
  Pending: 'gray',
  'In Progress': 'blue',
  Success: 'green',
  'Partial Success': 'amber',
  Error: 'red',
  'Timed Out': 'amber',
}

export function getDataImportRow(row: string, dataImport: DataImportRow) {
  if (row === 'status') {
    return {
      label: dataImport.status,
      color: statusColorMap[dataImport.status ?? ''] || 'gray',
    }
  }
  if (row === 'reference_doctype') {
    return {
      label: __(dataImport.reference_doctype),
      name: dataImport.reference_doctype,
    }
  }
  if (row === 'import_file') {
    // shows the short file name but filters on the stored path; a Google
    // Sheet has no file, so clicking it clears the file filter instead
    return {
      label:
        dataImport.import_file?.split('/').pop() ||
        dataImport.google_sheets_url ||
        '',
      name: dataImport.import_file || '',
    }
  }
  if (row === 'modified' || row === 'creation') {
    return timestampCell(dataImport[row])
  }
  return dataImport[row]
}

const importQueryKeys: (keyof ImportListQuery)[] = [
  'import',
  'import_field',
  'import_user',
  'import_from',
  'import_to',
]

// "Go to list" shows only what one import touched: records its user created
// (or, for updates, changed) between making the import and its last finish.
export function importListQuery(
  dataImport: Partial<DataImportDoc>,
): ImportListQuery {
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

export function importListFilters(query: ImportListQuery) {
  const { import_field, import_user, import_from, import_to } = query
  if (!query.import || !import_user || !import_from || !import_to) return {}
  const range = ['between', [import_from, import_to]]
  if (import_field === 'modified') {
    return { modified_by: import_user, modified: range }
  }
  return { owner: import_user, creation: range }
}

export function withoutImportQuery(query: Record<string, unknown>) {
  const rest = { ...query }
  for (const key of importQueryKeys) delete rest[key]
  return rest
}
