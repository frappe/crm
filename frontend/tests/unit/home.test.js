import {
  formatPercentChange,
  greetingFor,
  nextSort,
  recordListRoute,
  recordRoute,
  recordTitle,
  shortDuration,
  sortRows,
} from '@/utils/home'

const at = (hour) => new Date(2026, 9, 23, hour)

describe('nextSort', () => {
  const open = { key: 'open', align: 'right' }

  it('starts number columns with the highest first', () => {
    expect(nextSort({ key: 'user', descending: false }, open)).toEqual({
      key: 'open',
      descending: true,
    })
  })

  it('starts text columns from A', () => {
    expect(
      nextSort({ key: 'open', descending: true }, { key: 'user' }),
    ).toEqual({ key: 'user', descending: false })
  })

  it('flips the direction on a second click', () => {
    expect(nextSort({ key: 'open', descending: true }, open)).toEqual({
      key: 'open',
      descending: false,
    })
  })
})

describe('sortRows', () => {
  const value = (row) => row.time

  it('sorts both ways', () => {
    const rows = [{ time: 2 }, { time: 9 }, { time: 5 }]
    expect(sortRows(rows, { descending: true }, value).map(value)).toEqual([
      9, 5, 2,
    ])
    expect(sortRows(rows, { descending: false }, value).map(value)).toEqual([
      2, 5, 9,
    ])
  })

  it('keeps rows without a value last in either direction', () => {
    const rows = [{ time: null }, { time: 3 }, { time: 7 }]
    expect(sortRows(rows, { descending: true }, value).map(value)).toEqual([
      7,
      3,
      null,
    ])
    expect(sortRows(rows, { descending: false }, value).map(value)).toEqual([
      3,
      7,
      null,
    ])
  })

  it('sorts names alphabetically', () => {
    const name = (row) => row.name
    const rows = [{ name: 'Ravi' }, { name: 'Asha' }]
    expect(sortRows(rows, { descending: false }, name).map(name)).toEqual([
      'Asha',
      'Ravi',
    ])
  })
})

describe('greetingFor', () => {
  it('follows the time of day', () => {
    expect(greetingFor(at(9), 'Asha')).toBe('Good morning, Asha')
    expect(greetingFor(at(13), 'Asha')).toBe('Good afternoon, Asha')
    expect(greetingFor(at(20), 'Asha')).toBe('Good evening, Asha')
  })

  it('works without a name', () => {
    expect(greetingFor(at(9))).toBe('Good morning')
  })
})

describe('home records', () => {
  it('routes leads and deals to their pages', () => {
    expect(recordRoute({ doctype: 'CRM Deal', name: 'D-1' })).toEqual({
      name: 'Deal',
      params: { dealId: 'D-1' },
    })
    expect(recordRoute({ doctype: 'CRM Lead', name: 'L-1' })).toEqual({
      name: 'Lead',
      params: { leadId: 'L-1' },
    })
  })

  it('links to the list view of the doctype setting', () => {
    expect(recordListRoute('Both').name).toBe('Leads')
    expect(recordListRoute('Deal').name).toBe('Deals')
  })

  it('falls back to the contact name and then the ID', () => {
    expect(
      recordTitle({ title: 'Stripe', subtitle: 'Casey Brown', name: 'D-1' }),
    ).toBe('Stripe')
    expect(recordTitle({ subtitle: 'Casey Brown', name: 'D-1' })).toBe(
      'Casey Brown',
    )
    expect(recordTitle({ name: 'D-1' })).toBe('D-1')
  })
})

describe('shortDuration', () => {
  it('keeps the two largest units', () => {
    expect(shortDuration(30)).toBe('<1m')
    expect(shortDuration(45 * 60 + 20)).toBe('45m')
    expect(shortDuration(3 * 3600 + 20 * 60)).toBe('3h 20m')
    expect(shortDuration(2 * 86400 + 4 * 3600 + 59 * 60)).toBe('2d 4h')
  })

  it('drops an empty second unit', () => {
    expect(shortDuration(3 * 3600 + 30)).toBe('3h')
    expect(shortDuration(86400 + 5 * 60)).toBe('1d')
  })

  it('is blank without a value', () => {
    expect(shortDuration(null)).toBe('')
  })
})

describe('formatPercentChange', () => {
  it('rounds and caps the change', () => {
    expect(formatPercentChange(12.4)).toBe('12')
    expect(formatPercentChange(999)).toBe('999')
    expect(formatPercentChange(960461444)).toBe('999+')
  })
})
