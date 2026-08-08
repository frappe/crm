import {
  fuzzyScore,
  groupCommands,
  scoreCommand,
} from '@/utils/commandPalette'

describe('fuzzyScore', () => {
  it('ranks prefix, word, substring, and subsequence matches in order', () => {
    const prefix = fuzzyScore('Change status', 'change')
    const word = fuzzyScore('Set deal status', 'deal')
    const substring = fuzzyScore('Organization', 'gan')
    const subsequence = fuzzyScore('Organizations', 'orgs')
    expect(prefix).toBeGreaterThan(word)
    expect(word).toBeGreaterThan(substring)
    expect(substring).toBeGreaterThan(subsequence)
  })

  it('returns -1 when the query does not match', () => {
    expect(fuzzyScore('Deals', 'contact')).toBe(-1)
  })

  it('matches without regard to case or surrounding whitespace', () => {
    expect(fuzzyScore('  New Lead  ', 'NEW')).toBeGreaterThan(0)
  })
})

describe('scoreCommand', () => {
  it('uses keywords at a penalty', () => {
    const title = scoreCommand({ title: 'Create lead' }, 'create')
    const keyword = scoreCommand(
      { title: 'New lead', keywords: 'create add' },
      'create',
    )
    expect(title).toBeGreaterThan(keyword)
  })

  it('honors fixed ranks and contextual weights', () => {
    expect(scoreCommand({ title: 'Anything', rank: 2000 }, 'missing')).toBe(2000)
    const normal = scoreCommand({ title: 'Change status' }, 'status')
    const contextual = scoreCommand(
      { title: 'Change status', weight: 1.2 },
      'status',
    )
    expect(contextual).toBeGreaterThan(normal)
  })
})

describe('groupCommands', () => {
  const commands = [
    { id: 'leads', title: 'Leads', group: 'Navigate' },
    { id: 'deals', title: 'Deals', group: 'Navigate' },
    { id: 'new-deal', title: 'New deal', group: 'Create' },
  ]

  it('preserves group order while ranking within a group', () => {
    const groups = groupCommands(commands, 'deal')
    expect(groups.map((group) => group.title)).toEqual(['Navigate', 'Create'])
    expect(groups[0].items[0].id).toBe('deals')
  })

  it('hides flat option commands only for an empty query', () => {
    const hidden = {
      id: 'set-won',
      title: 'Set status: Won',
      group: 'Deal',
      hideWhenEmpty: true,
    }
    expect(groupCommands([hidden], '')).toEqual([])
    expect(groupCommands([hidden], 'won')[0].items[0]).toBe(hidden)
  })

  it('keeps source order for equal scores', () => {
    const groups = groupCommands(commands)
    expect(groups[0].items.map((command) => command.id)).toEqual([
      'leads',
      'deals',
    ])
  })
})
