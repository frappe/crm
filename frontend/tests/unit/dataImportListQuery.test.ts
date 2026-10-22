import { describe, expect, it, vi } from 'vitest'

vi.mock('@/composables/useTimelinePreferences', () => ({
  timestampCell: (date: string) => ({ label: date }),
}))

import {
  importListFilters,
  importListQuery,
  withoutImportQuery,
} from '@/utils/dataImport'

const dataImport = {
  name: 'DI-0001',
  owner: 'jane@example.com',
  creation: '2026-10-13 10:00:00',
  modified: '2026-10-13 10:05:00',
}

describe('importListQuery and importListFilters', () => {
  it('filters an insert import to the records its user created in its window', () => {
    const query = importListQuery({
      ...dataImport,
      import_type: 'Insert New Records',
    })
    expect(importListFilters(query)).toEqual({
      owner: 'jane@example.com',
      creation: ['between', ['2026-10-13 10:00:00', '2026-10-13 10:05:00']],
    })
  })

  it('filters an update import to the records its user changed in its window', () => {
    const query = importListQuery({
      ...dataImport,
      import_type: 'Update Existing Records',
    })
    expect(importListFilters(query)).toEqual({
      modified_by: 'jane@example.com',
      modified: ['between', ['2026-10-13 10:00:00', '2026-10-13 10:05:00']],
    })
  })

  it('adds no filter when the query has no complete import', () => {
    expect(importListFilters({})).toEqual({})
    expect(importListFilters({ import: 'DI-0001' })).toEqual({})
  })
})

describe('withoutImportQuery', () => {
  it('drops the import keys and keeps the rest', () => {
    const query = { view: 'my-view', ...importListQuery(dataImport) }
    expect(withoutImportQuery(query)).toEqual({ view: 'my-view' })
  })
})
