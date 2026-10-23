import { describe, expect, it } from 'vitest'
import { tableMultiselectFilters } from '@/utils/tableMultiselectFilters'

describe('Table MultiSelect filters', () => {
  it('preserves field constraints including an existing name condition', () => {
    const filters = { enabled: 1, name: ['like', 'CRM-%'] }
    expect(tableMultiselectFilters(filters, ['CRM-1'])).toEqual([
      ['enabled', '=', 1],
      ['name', 'like', 'CRM-%'],
      ['name', 'not in', ['CRM-1']],
    ])
    expect(filters).toEqual({ enabled: 1, name: ['like', 'CRM-%'] })
  })

  it('accepts JSON field filters', () => {
    expect(tableMultiselectFilters('{"enabled":1}', [])).toEqual([
      ['enabled', '=', 1],
      ['name', 'not in', []],
    ])
  })

  it('preserves array conditions and does not mutate either input', () => {
    const filters = [['Item Group', 'is_group', '=', 0]]
    const values = ['One']
    const result = tableMultiselectFilters(filters, values)
    expect(result).toEqual([...filters, ['name', 'not in', ['One']]])
    result.push(['enabled', '=', 1])
    result[1][2].push('Two')
    expect(filters).toEqual([['Item Group', 'is_group', '=', 0]])
    expect(values).toEqual(['One'])
  })

  it.each([null, undefined, '', '{invalid'])(
    'keeps duplicate exclusion with empty/invalid filters %s',
    (filters) => {
      expect(tableMultiselectFilters(filters, ['One'])).toEqual([
        ['name', 'not in', ['One']],
      ])
    },
  )
})
