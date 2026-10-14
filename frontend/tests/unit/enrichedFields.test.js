import { describe, it, expect } from 'vitest'
import { holdsEnrichedValue } from '@/data/enrichedFields'

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
