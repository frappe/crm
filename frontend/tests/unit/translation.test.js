import { describe, expect, it } from 'vitest'
import { translate } from '@/translation'

describe('translate', () => {
  it('fills placeholders from the values given', () => {
    expect(translate('New {0}, newest first', ['Deals'])).toBe(
      'New Deals, newest first',
    )
  })

  it('keeps placeholders when no values are given', () => {
    expect(translate('{0} waiting on a reply from you')).toBe(
      '{0} waiting on a reply from you',
    )
  })
})
