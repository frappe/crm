import { isMultiValueFilter, toFilterValueArray } from '@/utils/fieldTransforms'

// Regression coverage for #2125: "in" / "not in" used to render a plain text
// input for every field, so Select and Link filters lost the picker they get
// for "=" and values had to be typed comma-separated. The value now travels as
// an array, and a filter saved before this change still holds the old string.

const selectField = { fieldtype: 'Select', options: 'Open\nClosed' }
const checkField = { fieldtype: 'Check' }
const linkField = { fieldtype: 'Link', options: 'CRM Organization' }
const dynamicLinkField = {
  fieldtype: 'Dynamic Link',
  options: 'reference_type',
}
const dataField = { fieldtype: 'Data' }
const intField = { fieldtype: 'Int' }

describe('isMultiValueFilter', () => {
  it('picks a multi-select for the fieldtypes that can offer a list', () => {
    for (const operator of ['in', 'not in']) {
      expect(isMultiValueFilter(selectField, operator)).toBe(true)
      expect(isMultiValueFilter(checkField, operator)).toBe(true)
      expect(isMultiValueFilter(linkField, operator)).toBe(true)
    }
  })

  it('leaves fields with no option source on the text input', () => {
    for (const operator of ['in', 'not in']) {
      // Dynamic Link resolves its target doctype from a sibling field, so
      // there is nothing to search against here.
      expect(isMultiValueFilter(dynamicLinkField, operator)).toBe(false)
      expect(isMultiValueFilter(dataField, operator)).toBe(false)
      expect(isMultiValueFilter(intField, operator)).toBe(false)
    }
  })

  it('does not touch the operators that were already correct', () => {
    // "=" and "≠" have their own single-value controls; "like" stays free text
    // because its value is a pattern, not a member of a set.
    for (const operator of ['equals', '=', '!=', 'like', 'not like', 'is']) {
      expect(isMultiValueFilter(selectField, operator)).toBe(false)
      expect(isMultiValueFilter(linkField, operator)).toBe(false)
    }
  })

  it('survives a filter row whose field is not resolved yet', () => {
    expect(isMultiValueFilter(undefined, 'in')).toBe(false)
    expect(isMultiValueFilter({}, 'in')).toBe(false)
  })
})

describe('toFilterValueArray', () => {
  it('passes through the array the picker writes', () => {
    expect(toFilterValueArray(['Open', 'Qualified'])).toEqual([
      'Open',
      'Qualified',
    ])
  })

  it('restores a view saved with the legacy comma-separated string', () => {
    expect(toFilterValueArray('Open,Qualified')).toEqual(['Open', 'Qualified'])
    expect(toFilterValueArray('Open, Qualified , Junk')).toEqual([
      'Open',
      'Qualified',
      'Junk',
    ])
  })

  it('reads an unset filter as nothing selected', () => {
    // A blank entry would otherwise render as one checked value with an empty
    // label and count towards the "N selected" summary.
    expect(toFilterValueArray([''])).toEqual([])
    expect(toFilterValueArray('')).toEqual([])
    expect(toFilterValueArray(null)).toEqual([])
    expect(toFilterValueArray(undefined)).toEqual([])
  })
})

describe('restoring what the picker stored', () => {
  // The value reaches the list params as an array and comes back through
  // convertFilters on the next render, so restoring has to be idempotent.
  it('is stable for a Select selection', () => {
    const stored = ['Open', 'Qualified']
    expect(toFilterValueArray(toFilterValueArray(stored))).toEqual(stored)
  })

  it('is stable for a Check selection', () => {
    expect(toFilterValueArray(toFilterValueArray(['Yes']))).toEqual(['Yes'])
  })

  it('is stable for a Link selection', () => {
    const stored = ['Acme Corp', 'Globex']
    expect(toFilterValueArray(toFilterValueArray(stored))).toEqual(stored)
  })

  it('is stable for an empty selection', () => {
    expect(toFilterValueArray(toFilterValueArray([]))).toEqual([])
  })

  it('upgrades a legacy string once and then holds', () => {
    const restored = toFilterValueArray('Acme Corp,Globex')
    expect(restored).toEqual(['Acme Corp', 'Globex'])
    expect(toFilterValueArray(restored)).toEqual(restored)
  })
})
