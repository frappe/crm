import { describe, expect, it, vi } from 'vitest'

vi.mock('@/composables/useTimelinePreferences', () => ({
  timestampCell: (date: string) => ({ label: date, timeAgo: 'just now' }),
}))

import { getDataImportRow } from '@/utils/dataImport'

describe('getDataImportRow', () => {
  it('colours the status badge, with gray for an unknown status', () => {
    expect(getDataImportRow('status', { status: 'Error' })).toEqual({
      label: 'Error',
      color: 'red',
    })
    expect(getDataImportRow('status', { status: 'Other' })).toEqual({
      label: 'Other',
      color: 'gray',
    })
  })

  it('shows the file name but filters on the stored path', () => {
    expect(
      getDataImportRow('import_file', {
        import_file: '/private/files/crm_deals_500.csv',
      }),
    ).toEqual({
      label: 'crm_deals_500.csv',
      name: '/private/files/crm_deals_500.csv',
    })
  })

  it('shows the Google Sheet without filtering the file on its URL', () => {
    expect(
      getDataImportRow('import_file', {
        google_sheets_url: 'https://docs.google.com/spreadsheets/d/abc/edit',
      }),
    ).toEqual({
      label: 'https://docs.google.com/spreadsheets/d/abc/edit',
      name: '',
    })
    expect(getDataImportRow('import_file', {})).toEqual({ label: '', name: '' })
  })

  it('shows modified as a timestamp cell and other fields as they are', () => {
    expect(getDataImportRow('modified', { modified: '2026-10-13' })).toEqual({
      label: '2026-10-13',
      timeAgo: 'just now',
    })
    expect(getDataImportRow('import_type', { import_type: 'Insert' })).toBe(
      'Insert',
    )
  })
})
