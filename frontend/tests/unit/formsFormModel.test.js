import { describe, expect, it } from 'vitest'
import {
  buildSections,
  flattenSections,
  groupLayout,
  newFieldFromCatalog,
  optionList,
  slugify,
} from '../../../crm/fcrm/frontend/forms/builder/formModel.js'

const field = (fieldname) => ({ fieldname, fieldtype: 'Data' })
const section = (fieldname) => ({ fieldname, fieldtype: 'Section Break' })
const column = (fieldname) => ({ fieldname, fieldtype: 'Column Break' })

describe('form model', () => {
  it('slugifies a title', () => {
    expect(slugify('  Contact Us!  ')).toBe('contact-us')
  })

  it('gives fields before the first break a section of their own', () => {
    const sections = buildSections([field('a'), section('s1'), field('b')])
    expect(sections).toHaveLength(2)
    expect(sections[0].columns[0].items.map((f) => f.fieldname)).toEqual(['a'])
    expect(sections[1].secField.fieldname).toBe('s1')
  })

  it('builds one empty section for an empty form', () => {
    expect(buildSections([])).toHaveLength(1)
  })

  it('flattens sections and columns back to the same order', () => {
    const fields = [section('s1'), field('a'), column('c1'), field('b'), section('s2')]
    expect(flattenSections(buildSections(fields)).map((f) => f.fieldname)).toEqual([
      's1',
      'a',
      'c1',
      'b',
      's2',
    ])
  })

  it('groups the preview layout and drops empty sections', () => {
    const layout = groupLayout([field('a'), column('c'), field('b'), section('s')])
    expect(layout).toHaveLength(1)
    expect(layout[0].columns.map((c) => c.length)).toEqual([1, 1])
  })

  it('builds a blank form field from a catalog entry', () => {
    const f = newFieldFromCatalog({ fieldname: 'status', label: 'Status', fieldtype: 'Select', options: 'A\nB', reqd: 1 })
    expect(f).toMatchObject({ fieldname: 'status', reqd: true, placeholder: '', depends_on: '' })
  })

  it('splits Select options and skips blanks', () => {
    expect(optionList('A\n\nB')).toEqual(['A', 'B'])
    expect(optionList(undefined)).toEqual([])
  })
})
