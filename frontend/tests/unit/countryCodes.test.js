import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  formatCountryList,
  getCountryEmoji,
  getCountryByISD,
  matchCountryByPrefix,
  getDefaultCountry,
  parsePhoneNumber,
  formatPhoneNumber,
} from '@/utils/countryCodes'

const sampleCountryInfo = {
  Afghanistan: { code: 'af', isd: '+93' },
  Canada: { code: 'ca', isd: '+1' },
  India: { code: 'in', isd: '+91' },
  'United States': { code: 'us', isd: '+1' },
  Germany: { code: 'de', isd: '+49' },
}

describe('countryCodes utility', () => {
  const countries = formatCountryList(sampleCountryInfo)

  describe('formatCountryList', () => {
    it('transforms raw country_info map into normalized sorted country objects', () => {
      expect(countries.length).toBe(5)
      expect(countries[0].country).toBe('Afghanistan')
      expect(countries.find((c) => c.country === 'India')).toEqual({
        country: 'India',
        isd: '+91',
        code: 'in',
      })
    })

    it('cleans up spaces in ISD codes and lowercases country codes', () => {
      const raw = {
        'Cayman Islands': { code: 'KY', isd: '+ 345' },
      }
      const list = formatCountryList(raw)
      expect(list[0]).toEqual({
        country: 'Cayman Islands',
        isd: '+345',
        code: 'ky',
      })
    })
  })

  describe('getCountryEmoji', () => {
    it('returns the correct flag emoji for valid 2-letter codes', () => {
      expect(getCountryEmoji('in')).toBe('🇮🇳')
      expect(getCountryEmoji('IN')).toBe('🇮🇳')
      expect(getCountryEmoji('us')).toBe('🇺🇸')
      expect(getCountryEmoji('gb')).toBe('🇬🇧')
      expect(getCountryEmoji('de')).toBe('🇩🇪')
    })

    it('returns fallback globe for invalid or missing codes', () => {
      expect(getCountryEmoji('')).toBe('🌐')
      expect(getCountryEmoji(null)).toBe('🌐')
      expect(getCountryEmoji(undefined)).toBe('🌐')
      expect(getCountryEmoji('usa')).toBe('🌐')
    })
  })

  describe('lookup helpers', () => {
    it('finds country by ISD code', () => {
      expect(getCountryByISD('+91', countries)?.country).toBe('India')
      expect(getCountryByISD('91', countries)?.country).toBe('India')
      expect(getCountryByISD('+999999', countries)).toBeNull()
    })

    it('matches country by phone prefix (longest match)', () => {
      const match = matchCountryByPrefix('+919876543210', countries)
      expect(match?.code).toBe('in')
      expect(match?.isd).toBe('+91')
    })
  })

  describe('getDefaultCountry', () => {
    const originalSysdefaults = window.sysdefaults

    beforeEach(() => {
      window.sysdefaults = {}
    })

    afterEach(() => {
      window.sysdefaults = originalSysdefaults
    })

    it('defaults to US when no default is specified or configured', () => {
      const country = getDefaultCountry(null, countries)
      expect(country.code).toBe('us')
    })

    it('uses window.sysdefaults.country if configured', () => {
      window.sysdefaults = { country: 'India' }
      const country = getDefaultCountry(null, countries)
      expect(country.code).toBe('in')
    })

    it('respects explicitly provided default country name or code', () => {
      expect(getDefaultCountry('Germany', countries).code).toBe('de')
      expect(getDefaultCountry('in', countries).code).toBe('in')
      expect(getDefaultCountry('+91', countries).code).toBe('in')
    })
  })

  describe('parsePhoneNumber', () => {
    it('parses standard Frappe hyphenated phone format (+ISD-NUMBER)', () => {
      const parsed = parsePhoneNumber('+91-9876543210', null, countries)
      expect(parsed.country.code).toBe('in')
      expect(parsed.phone).toBe('9876543210')
    })

    it('parses hyphenated phone without leading + (ISD-NUMBER)', () => {
      const parsed = parsePhoneNumber('91-9876543210', null, countries)
      expect(parsed.country.code).toBe('in')
      expect(parsed.phone).toBe('9876543210')
    })

    it('parses international number starting with + without hyphen', () => {
      const parsed = parsePhoneNumber('+919876543210', null, countries)
      expect(parsed.country.code).toBe('in')
      expect(parsed.phone).toBe('9876543210')
    })

    it('handles phone number with spaces after ISD', () => {
      const parsed = parsePhoneNumber('+91 9876543210', null, countries)
      expect(parsed.country.code).toBe('in')
      expect(parsed.phone).toBe('9876543210')
    })

    it('parses plain local number using default country', () => {
      const parsed = parsePhoneNumber('9876543210', 'India', countries)
      expect(parsed.country.code).toBe('in')
      expect(parsed.phone).toBe('9876543210')
    })

    it('returns empty phone and default country for empty/null input', () => {
      const parsedEmpty = parsePhoneNumber('', null, countries)
      expect(parsedEmpty.phone).toBe('')
      expect(parsedEmpty.country.code).toBe('us')

      const parsedNull = parsePhoneNumber(null, 'India', countries)
      expect(parsedNull.phone).toBe('')
      expect(parsedNull.country.code).toBe('in')
    })

    it('respects preferred country when ISD is shared (+1 for Canada)', () => {
      const parsedCanada = parsePhoneNumber('+1-5551234', 'Canada', countries)
      expect(parsedCanada.country.code).toBe('ca')
      expect(parsedCanada.phone).toBe('5551234')

      const parsedUS = parsePhoneNumber(
        '+1-5551234',
        'United States',
        countries,
      )
      expect(parsedUS.country.code).toBe('us')
      expect(parsedUS.phone).toBe('5551234')
    })

    it('simulates async countries resolution for unhyphenated numbers (+919876543210)', () => {
      // Step 1: Component mounts before async country list loads (countries = [])
      const initial = parsePhoneNumber('+919876543210', null, [])
      expect(initial.phone).toBe('+919876543210')

      // Step 2: Once async country list resolves, re-parsing yields the stripped phone and matched country
      const resolved = parsePhoneNumber(
        '+919876543210',
        initial.country,
        countries,
      )
      expect(resolved.country.code).toBe('in')
      expect(resolved.phone).toBe('9876543210')
    })
  })

  describe('formatPhoneNumber', () => {
    it('formats country and phone as +<ISD>-<number>', () => {
      const country = { isd: '+91', country: 'India', code: 'in' }
      expect(formatPhoneNumber(country, '9876543210')).toBe('+91-9876543210')
    })

    it('returns empty string if phone is empty or null', () => {
      const country = { isd: '+91', country: 'India', code: 'in' }
      expect(formatPhoneNumber(country, '')).toBe('')
      expect(formatPhoneNumber(country, null)).toBe('')
      expect(formatPhoneNumber(country, undefined)).toBe('')
    })

    it('returns phone as-is if it already starts with +', () => {
      const country = { isd: '+91', country: 'India', code: 'in' }
      expect(formatPhoneNumber(country, '+91-9876543210')).toBe(
        '+91-9876543210',
      )
    })

    it('strips leading hyphens from phone number before formatting', () => {
      const country = { isd: '+91', country: 'India', code: 'in' }
      expect(formatPhoneNumber(country, '-9876543210')).toBe('+91-9876543210')
    })

    it('returns plain phone if country is missing', () => {
      expect(formatPhoneNumber(null, '9876543210')).toBe('9876543210')
    })
  })
})
