import {
  DONT_IMPORT,
  describeFailedRow,
  getColumnMappings,
  getUnmappedRequiredFields,
  groupInvitesByRole,
  isLeadNameMapped,
  toColumnToFieldMap,
} from '@/utils/setup'

const preview = {
  columns: [
    { header_title: 'Sr. No', skip_import: true },
    { header_title: 'First Name', df: { fieldname: 'first_name' } },
    { header_title: 'Notes', skip_import: true },
    { header_title: 'Mail', df: { fieldname: 'email' } },
  ],
}

describe('getColumnMappings', () => {
  it('skips the serial column and uses 0-based file indexes', () => {
    expect(getColumnMappings(preview)).toEqual([
      { index: 0, header: 'First Name', fieldname: 'first_name' },
      { index: 1, header: 'Notes', fieldname: '' },
      { index: 2, header: 'Mail', fieldname: 'email' },
    ])
  })

  it('returns nothing without a preview', () => {
    expect(getColumnMappings(null)).toEqual([])
  })
})

describe('toColumnToFieldMap', () => {
  it('marks unmapped columns as not imported', () => {
    expect(toColumnToFieldMap(getColumnMappings(preview))).toEqual({
      0: 'first_name',
      1: DONT_IMPORT,
      2: 'email',
    })
  })
})

describe('getUnmappedRequiredFields', () => {
  const fields = [
    { fieldname: 'first_name', reqd: 1 },
    { fieldname: 'territory', reqd: 1 },
    { fieldname: 'source', reqd: 1, default: 'Web' },
    { fieldname: 'email', reqd: 0 },
  ]

  it('lists required fields without a default that nothing maps to', () => {
    const result = getUnmappedRequiredFields(fields, getColumnMappings(preview))
    expect(result.map((f) => f.fieldname)).toEqual(['territory'])
  })
})

describe('isLeadNameMapped', () => {
  it('requires a column mapped to first name', () => {
    const mappings = getColumnMappings(preview)
    expect(isLeadNameMapped(mappings)).toBe(true)
    expect(isLeadNameMapped(mappings.slice(1))).toBe(false)
  })
})

describe('groupInvitesByRole', () => {
  it('groups trimmed emails by role, skipping blanks and duplicates', () => {
    const rows = [
      { email: ' Ann@Example.com ', role: 'Sales User' },
      { email: '', role: 'Sales User' },
      { email: 'ann@example.com', role: 'Sales Manager' },
      { email: 'bob@example.com', role: 'Sales Manager' },
    ]
    expect(groupInvitesByRole(rows)).toEqual({
      'Sales User': ['ann@example.com'],
      'Sales Manager': ['bob@example.com'],
    })
  })
})

describe('describeFailedRow', () => {
  it('reads the data row number and a plain-text message', () => {
    const log = {
      row_indexes: '[3]',
      messages: JSON.stringify([{ message: 'Value missing for <b>Email</b>' }]),
    }
    expect(describeFailedRow(log)).toEqual({
      row: 2,
      message: 'Value missing for Email',
    })
  })

  it('falls back when the log has no usable details', () => {
    expect(describeFailedRow({ row_indexes: 'x', messages: null })).toEqual({
      row: null,
      message: 'Failed to import',
    })
  })
})
