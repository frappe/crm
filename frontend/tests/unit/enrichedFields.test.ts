import { describe, it, expect, vi } from 'vitest'
import { editedToReplace, holdsEnrichedValue } from '@/data/enrichedFields'

// document.js pulls in dialogs.jsx, which vitest can't compile.
vi.mock('@/data/document', () => ({ useDocument: () => ({}) }))

describe('holdsEnrichedValue', () => {
  it('matches the value enrichment wrote', () => {
    const field = { fieldname: 'linkedin', value: 'https://x.example' }
    expect(holdsEnrichedValue({ linkedin: 'https://x.example' }, field)).toBe(
      true,
    )
  })

  it('stops matching once the field is edited', () => {
    const field = { fieldname: 'linkedin', value: 'https://x.example' }
    expect(holdsEnrichedValue({ linkedin: 'https://y.example' }, field)).toBe(
      false,
    )
    expect(holdsEnrichedValue({ linkedin: '' }, field)).toBe(false)
  })

  it('treats a whole-number float as equal to its integer', () => {
    // The API casts to float; JSON drops the ".0" either way.
    const field = { fieldname: 'annual_revenue', value: 9000.0 }
    expect(holdsEnrichedValue({ annual_revenue: 9000 }, field)).toBe(true)
  })

  it('treats null and empty string as the same', () => {
    const field = { fieldname: 'industry', value: null }
    expect(holdsEnrichedValue({ industry: '' }, field)).toBe(true)
  })
})

describe('editedToReplace', () => {
  const field = (label: string, edited: boolean, refreshes: boolean) => ({
    fieldname: label.toLowerCase(),
    label,
    value: 'x',
    edited,
    refreshes,
  })

  it('lists edited fields that re-enriching overwrites', () => {
    expect(
      editedToReplace([
        field('Industry', true, true),
        field('LinkedIn', true, false),
        field('Website', false, true),
      ]),
    ).toEqual(['Industry'])
  })

  it('is empty when nothing edited would be replaced', () => {
    expect(editedToReplace([field('LinkedIn', false, false)])).toEqual([])
    expect(editedToReplace([])).toEqual([])
  })
})
