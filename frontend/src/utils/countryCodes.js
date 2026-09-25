export function getCountryEmoji(code) {
  if (!code || typeof code !== 'string' || code.length !== 2) return '🌐'
  const codePoints = code
    .toUpperCase()
    .split('')
    .map((c) => 127397 + c.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

export function formatCountryList(countryInfoMap = {}) {
  return Object.entries(countryInfoMap)
    .map(([country, info]) => ({
      country,
      isd: info?.isd
        ? info.isd.startsWith('+')
          ? info.isd.replace(/\s+/g, '')
          : '+' + String(info.isd).trim()
        : '',
      code: info?.code ? String(info.code).toLowerCase() : '',
    }))
    .filter((c) => c.isd && c.code)
    .sort((a, b) => a.country.localeCompare(b.country))
}

export function getCountryByISD(isd, countries = [], preferredCountry = null) {
  if (!isd || !countries.length) return null
  const normalized = isd.startsWith('+') ? isd : '+' + isd
  if (preferredCountry && preferredCountry.isd === normalized) {
    return preferredCountry
  }
  const matches = countries.filter((c) => c.isd === normalized)
  if (!matches.length) return null
  if (matches.length === 1) return matches[0]
  const usMatch = matches.find((c) => c.code === 'us')
  if (usMatch) return usMatch
  return matches[0]
}

export function matchCountryByPrefix(
  str,
  countries = [],
  preferredCountry = null,
) {
  if (!str || !str.startsWith('+') || !countries.length) return null
  if (preferredCountry && str.startsWith(preferredCountry.isd)) {
    return preferredCountry
  }
  for (let len = 5; len >= 2; len--) {
    const prefix = str.slice(0, len)
    const match = getCountryByISD(prefix, countries, preferredCountry)
    if (match) return match
  }
  return null
}

export function getDefaultCountry(defaultNameOrCode, countries = []) {
  if (
    defaultNameOrCode &&
    typeof defaultNameOrCode === 'object' &&
    defaultNameOrCode.code
  ) {
    return defaultNameOrCode
  }
  const fallback = { country: 'United States', isd: '+1', code: 'us' }
  if (!countries.length) return fallback

  const query =
    defaultNameOrCode ||
    (typeof window !== 'undefined' && window.sysdefaults?.country)
  if (query && typeof query === 'string') {
    const qLower = query.toLowerCase()
    const match =
      countries.find((c) => c.country.toLowerCase() === qLower) ||
      countries.find((c) => c.code === qLower) ||
      countries.find((c) => c.isd === query || c.isd === '+' + query)
    if (match) return match
  }

  return countries.find((c) => c.code === 'us') || countries[0] || fallback
}

export function parsePhoneNumber(raw, defaultCountry, countries = []) {
  const fallback = getDefaultCountry(defaultCountry, countries)
  if (!raw) {
    return { country: fallback, phone: '' }
  }

  const str = String(raw).trim()

  // 1. Explicit hyphen format: "+91-9876543210" or "91-9876543210"
  if (str.includes('-')) {
    const parts = str.split('-')
    const isd = parts[0].startsWith('+') ? parts[0] : '+' + parts[0]
    const matched = getCountryByISD(isd, countries, fallback)
    if (matched) {
      return { country: matched, phone: parts.slice(1).join('-').trim() }
    }
    // If countries list not loaded yet or unknown ISD, preserve ISD
    if (/^\+\d+$/.test(isd)) {
      return {
        country: { country: isd, isd, code: '' },
        phone: parts.slice(1).join('-').trim(),
      }
    }
  }

  // 2. Starts with "+" without hyphen: "+919876543210"
  if (str.startsWith('+')) {
    const matched = matchCountryByPrefix(str, countries, fallback)
    if (matched) {
      const phonePart = str.slice(matched.isd.length).replace(/^[\s-]+/, '')
      return { country: matched, phone: phonePart }
    }
  }

  // 3. Plain number without country code
  return { country: fallback, phone: str }
}

export function formatPhoneNumber(country, phone) {
  let cleanPhone = phone ? String(phone).trim() : ''
  if (!cleanPhone) return ''
  if (cleanPhone.startsWith('+')) {
    return cleanPhone
  }
  cleanPhone = cleanPhone.replace(/^-+/, '').trim()
  if (!cleanPhone) return ''
  if (country && country.isd) {
    return `${country.isd}-${cleanPhone}`
  }
  return cleanPhone
}
