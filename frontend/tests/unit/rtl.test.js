import {
  RTL_LANGUAGES,
  applyDocumentDirection,
  isRtlLanguage,
  normalizeLanguage,
  resolveBootLanguage,
} from '@/utils/rtl'

describe('normalizeLanguage', () => {
  it('returns the primary subtag in lowercase', () => {
    expect(normalizeLanguage('AR')).toBe('ar')
    expect(normalizeLanguage('ar-SA')).toBe('ar')
    expect(normalizeLanguage('he_IL')).toBe('he')
  })

  it('returns empty for missing values', () => {
    expect(normalizeLanguage('')).toBe('')
    expect(normalizeLanguage(null)).toBe('')
    expect(normalizeLanguage(undefined)).toBe('')
  })
})

describe('isRtlLanguage', () => {
  it.each(RTL_LANGUAGES)('treats %s as RTL', (lang) => {
    expect(isRtlLanguage(lang)).toBe(true)
  })

  it('treats regional Arabic as RTL', () => {
    expect(isRtlLanguage('ar-SA')).toBe(true)
  })

  it('treats English and Hindi as LTR', () => {
    expect(isRtlLanguage('en')).toBe(false)
    expect(isRtlLanguage('hi')).toBe(false)
  })
})

describe('resolveBootLanguage', () => {
  it('prefers boot.lang over sysdefaults', () => {
    expect(
      resolveBootLanguage({
        lang: 'ar',
        sysdefaults: { language: 'en' },
      }),
    ).toBe('ar')
  })

  it('falls back to sysdefaults.language', () => {
    expect(resolveBootLanguage({ sysdefaults: { language: 'he' } })).toBe('he')
  })

  it('returns empty when boot has no language', () => {
    expect(resolveBootLanguage({})).toBe('')
  })
})

describe('applyDocumentDirection', () => {
  it('sets dir=rtl and lang on the root for Arabic', () => {
    const root = { lang: 'en', setAttribute: vi.fn() }
    expect(applyDocumentDirection('ar', root)).toEqual({ lang: 'ar', dir: 'rtl' })
    expect(root.lang).toBe('ar')
    expect(root.setAttribute).toHaveBeenCalledWith('dir', 'rtl')
  })

  it('sets dir=ltr for English', () => {
    const root = { lang: 'ar', setAttribute: vi.fn() }
    expect(applyDocumentDirection('en', root)).toEqual({ lang: 'en', dir: 'ltr' })
    expect(root.setAttribute).toHaveBeenCalledWith('dir', 'ltr')
  })

  it('defaults to English LTR when language is missing', () => {
    const root = { setAttribute: vi.fn() }
    expect(applyDocumentDirection('', root)).toEqual({ lang: 'en', dir: 'ltr' })
  })
})
