import {
  RECENT_LIMIT,
  readRecent,
  rememberRoute,
  sortByRecency,
} from '@/utils/recentRecords'

const visit = (name, id, user = 'asha@example.com') =>
  rememberRoute({ name, params: { [`${name.toLowerCase()}Id`]: id } }, user)

describe('recent records', () => {
  beforeEach(() => localStorage.clear())

  it('keeps the last opened leads and deals, newest first', () => {
    visit('Lead', 'L-1')
    visit('Deal', 'D-1')
    visit('Lead', 'L-1')
    visit('Contact', 'C-1')
    expect(readRecent('asha@example.com')).toEqual([
      { doctype: 'CRM Lead', name: 'L-1' },
      { doctype: 'CRM Deal', name: 'D-1' },
    ])
  })

  it('is per user and capped', () => {
    for (let i = 0; i < RECENT_LIMIT + 2; i++) visit('Lead', `L-${i}`)
    expect(readRecent('asha@example.com')).toHaveLength(RECENT_LIMIT)
    expect(readRecent('ravi@example.com')).toEqual([])
  })

  it('sorts fetched records by recency', () => {
    const recent = [
      { doctype: 'CRM Deal', name: 'D-1' },
      { doctype: 'CRM Lead', name: 'L-1' },
    ]
    const records = [
      { doctype: 'CRM Lead', name: 'L-1' },
      { doctype: 'CRM Deal', name: 'D-1' },
    ]
    expect(sortByRecency(records, recent).map((r) => r.name)).toEqual([
      'D-1',
      'L-1',
    ])
  })
})
