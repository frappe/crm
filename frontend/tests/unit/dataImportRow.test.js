vi.mock('@/composables/useTimelinePreferences', () => ({
  timestampCell: (date) => ({ label: date, timeAgo: 'just now' }),
}))

import { getDataImportRow } from '@/utils/dataImport'

describe('getDataImportRow', () => {
  it('colours the status badge, with gray for an unknown status', () => {
    expect(getDataImportRow('status', { status: 'Error' })).toEqual({
      label: 'Error',
      color: 'red',
    })
    expect(getDataImportRow('status', { status: 'Other' }).color).toBe('gray')
  })

  it('shows the file name, or the Google Sheet when there is no file', () => {
    expect(
      getDataImportRow('import_file', {
        import_file: '/private/files/crm_deals_500.csv',
      }),
    ).toBe('crm_deals_500.csv')
    expect(
      getDataImportRow('import_file', {
        google_sheets_url: 'https://docs.google.com/spreadsheets/d/abc/edit',
      }),
    ).toBe('https://docs.google.com/spreadsheets/d/abc/edit')
    expect(getDataImportRow('import_file', {})).toBe('')
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
