import { mergeFormTabs, filterVisibleTabs } from '@/utils/formTabs'

const base = [
  { name: 'Activity', label: 'Activity' },
  { name: 'Emails', label: 'Emails' },
]

describe('mergeFormTabs', () => {
  it('returns a copy of base tabs when there are no script tabs', () => {
    const result = mergeFormTabs(base, [])
    expect(result).toEqual(base)
    expect(result).not.toBe(base)
    expect(result[0]).not.toBe(base[0])
  })

  it('appends a new script tab after the built-in tabs', () => {
    const result = mergeFormTabs(base, [{ name: 'Excom', label: 'Excom' }])
    expect(result.map((t) => t.name)).toEqual(['Activity', 'Emails', 'Excom'])
  })

  it('patches a built-in tab in place when names match', () => {
    const result = mergeFormTabs(base, [{ name: 'Emails', label: 'Inbox' }])
    expect(result).toHaveLength(2)
    expect(result[1]).toEqual({ name: 'Emails', label: 'Inbox' })
  })

  it('never mutates either input', () => {
    const baseCopy = JSON.parse(JSON.stringify(base))
    const scriptTabs = [{ name: 'Excom', label: 'Excom' }]
    const scriptCopy = JSON.parse(JSON.stringify(scriptTabs))
    mergeFormTabs(base, scriptTabs)
    expect(base).toEqual(baseCopy)
    expect(scriptTabs).toEqual(scriptCopy)
  })

  it('ignores malformed script tabs', () => {
    const result = mergeFormTabs(base, [
      null,
      undefined,
      'Excom',
      42,
      {},
      { label: 'No name' },
      { name: 42 },
      { name: 'Valid' },
    ])
    expect(result.map((t) => t.name)).toEqual(['Activity', 'Emails', 'Valid'])
  })

  it('keeps the first definition when a script pushes the same name twice', () => {
    const result = mergeFormTabs(base, [
      { name: 'Excom', label: 'One' },
      { name: 'Excom', label: 'Two' },
    ])
    expect(result).toHaveLength(3)
    expect(result[2].label).toBe('Two')
  })

  it('tolerates non-array arguments', () => {
    expect(mergeFormTabs(undefined, undefined)).toEqual([])
    expect(mergeFormTabs(null, null)).toEqual([])
    expect(mergeFormTabs(base, 'nope').map((t) => t.name)).toEqual([
      'Activity',
      'Emails',
    ])
  })

  it('preserves a component reference without cloning it', () => {
    const component = { render: () => null }
    const result = mergeFormTabs(base, [{ name: 'Excom', component }])
    expect(result[2].component).toBe(component)
  })
})

describe('filterVisibleTabs', () => {
  it('keeps tabs without a condition', () => {
    expect(filterVisibleTabs(base)).toHaveLength(2)
  })

  it('applies truthy and falsy conditions', () => {
    const tabs = [
      { name: 'A', condition: () => true },
      { name: 'B', condition: () => false },
      { name: 'C' },
    ]
    expect(filterVisibleTabs(tabs).map((t) => t.name)).toEqual(['A', 'C'])
  })

  it('hides a tab whose condition throws, without breaking the rest', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const tabs = [
      {
        name: 'Boom',
        condition: () => {
          throw new Error('nope')
        },
      },
      { name: 'Fine' },
    ]
    expect(filterVisibleTabs(tabs).map((t) => t.name)).toEqual(['Fine'])
    expect(spy).toHaveBeenCalled()
    spy.mockRestore()
  })

  it('ignores a non-function condition', () => {
    expect(filterVisibleTabs([{ name: 'A', condition: 'yes' }])).toHaveLength(1)
  })

  it('tolerates non-array input', () => {
    expect(filterVisibleTabs(undefined)).toEqual([])
    expect(filterVisibleTabs(null)).toEqual([])
  })
})
