import {
  fieldColumn,
  keepAvailable,
  resolveColumns,
  toSavedColumns,
} from '@/components/Home/columns'

const defaults = [
  { key: 'title', label: 'Name', width: 'minmax(0,3fr)' },
  { key: 'status', label: 'Status', type: 'status', width: 'minmax(0,2fr)' },
  { key: 'awaiting_reply_since', label: 'Waiting since', width: '6rem' },
]

const fields = {
  annual_revenue: {
    fieldname: 'annual_revenue',
    label: 'Annual Revenue',
    fieldtype: 'Currency',
    options: 'currency',
  },
  owner: {
    fieldname: 'owner',
    label: 'Owner',
    fieldtype: 'Link',
    options: 'User',
  },
  territory: { fieldname: 'territory', label: 'Territory', fieldtype: 'Link' },
}

const keys = (columns) => columns.map((column) => column.key)

describe('home widget columns', () => {
  it('shows the defaults until columns are saved', () => {
    expect(resolveColumns(defaults, undefined, fields)).toBe(defaults)
  })

  it('follows the saved order and overrides', () => {
    const columns = resolveColumns(
      defaults,
      [
        { key: 'awaiting_reply_since' },
        { key: 'title', label: 'Who', width: '2' },
        { key: 'annual_revenue' },
      ],
      fields,
    )
    expect(keys(columns)).toEqual([
      'awaiting_reply_since',
      'title',
      'annual_revenue',
    ])
    expect(columns[1]).toMatchObject({ label: 'Who', width: 'minmax(0,2fr)' })
    expect(columns[2]).toMatchObject({
      type: 'field',
      align: 'right',
      width: '7rem',
    })
  })

  it('skips saved columns that are no longer available', () => {
    const saved = [{ key: 'title' }, { key: 'deal_value' }]
    expect(keys(resolveColumns(defaults, saved, fields))).toEqual(['title'])
    expect(keepAvailable(saved, defaults, fields)).toEqual([{ key: 'title' }])
  })

  it('renders user links with an avatar', () => {
    expect(fieldColumn(fields.owner).type).toBe('user')
    expect(fieldColumn(fields.territory).type).toBe('field')
  })

  it('stores only what differs from a default', () => {
    const columns = [
      { ...defaults[0], label: 'Who' },
      { ...defaults[2] },
      { ...fieldColumn(fields.territory), width: '12rem' },
    ]
    expect(toSavedColumns(columns, defaults, fields)).toEqual([
      { key: 'title', label: 'Who' },
      { key: 'awaiting_reply_since' },
      { key: 'territory', width: '12rem' },
    ])
  })
})
