import { activityCommand } from '@/components/CommandPalette/activityCommands'
import { groupCommands } from '@/utils/commandPalette'

const hits = [
  {
    source_doctype: 'Comment',
    source_name: 'c1',
    parent_title: 'Zeta Corp',
    title: '',
    snippet: 'annual <mark>pricing</mark>',
    route: 'Deal',
    hash: 'c1',
  },
  {
    source_doctype: 'Communication',
    source_name: 'e1',
    parent_title: 'Acme',
    title: 'Re: <mark>Pricing</mark>',
    snippet: 'enterprise <mark>pricing</mark> tier',
    route: 'Lead',
    hash: 'e1',
  },
]

const commands = hits.map((hit) => activityCommand(hit, () => {}))

describe('activityCommand', () => {
  it('labels the source and record type', () => {
    expect(commands.map((command) => command.subtitle)).toEqual([
      'Deal · Comment',
      'Lead · Email',
    ])
  })

  it('adds the email subject to the record title without marks', () => {
    expect(commands.map((command) => command.title)).toEqual([
      'Zeta Corp',
      'Acme — Re: Pricing',
    ])
  })

  it('opens the hit it was built from', () => {
    const open = vi.fn()
    activityCommand(hits[1], open).perform()
    expect(open).toHaveBeenCalledWith(hits[1])
  })
})

describe('activity ranking', () => {
  const record = { id: 'record', title: 'Pricing Partners', group: 'Records' }

  it('keeps server order after records, even for typo matches', () => {
    const groups = groupCommands([...commands, record], 'pricng')
    expect(groups.map((group) => group.title)).toEqual([
      'Records',
      'In activity',
    ])
    expect(groups[1].items.map((command) => command.id)).toEqual([
      'activity-Comment-c1',
      'activity-Communication-e1',
    ])
  })

  it('keeps hits whose text does not contain the query', () => {
    const [group] = groupCommands(commands, 'xyz')
    expect(group.items).toHaveLength(2)
  })
})
