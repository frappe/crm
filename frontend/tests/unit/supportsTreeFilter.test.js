import { supportsTreeFilter } from '@/utils/fieldTransforms'

// #2209: filtering by a parent territory should also match its child
// territories. "descendants of (inclusive)" does that, but only makes sense for
// a Link to a tree doctype, which get_filterable_fields flags with `is_tree`.

describe('supportsTreeFilter', () => {
  it('offers the hierarchy operator for a Link to a tree doctype', () => {
    const territory = {
      fieldtype: 'Link',
      options: 'CRM Territory',
      is_tree: true,
    }
    expect(supportsTreeFilter(territory)).toBe(true)
  })

  it('leaves a Link to a flat doctype alone', () => {
    const owner = { fieldtype: 'Link', options: 'User', is_tree: false }
    expect(supportsTreeFilter(owner)).toBe(false)
  })

  it('treats a field without the flag as flat', () => {
    expect(
      supportsTreeFilter({ fieldtype: 'Link', options: 'CRM Territory' }),
    ).toBe(false)
  })

  it('ignores non-Link fields even if flagged', () => {
    expect(supportsTreeFilter({ fieldtype: 'Data', is_tree: true })).toBe(false)
    expect(
      supportsTreeFilter({ fieldtype: 'Dynamic Link', is_tree: true }),
    ).toBe(false)
  })

  it('handles a missing field', () => {
    expect(supportsTreeFilter(undefined)).toBe(false)
    expect(supportsTreeFilter(null)).toBe(false)
  })
})
