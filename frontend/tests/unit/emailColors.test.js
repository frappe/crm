import {
  DARK_SURFACE,
  parseRgb,
  toCss,
  contrast,
  invertLightness,
  darkModeBackground,
  darkModeText,
} from '@/utils/emailColors'

const rgb = (r, g, b, a = 1) => ({ r, g, b, a })

describe('parseRgb', () => {
  it('reads computed rgb and rgba values', () => {
    expect(parseRgb('rgb(34, 34, 34)')).toEqual(rgb(34, 34, 34))
    expect(parseRgb('rgba(0, 0, 0, 0)')).toEqual(rgb(0, 0, 0, 0))
  })

  it('returns null for anything else', () => {
    expect(parseRgb('black')).toBeNull()
    expect(parseRgb('')).toBeNull()
    expect(parseRgb(undefined)).toBeNull()
  })
})

describe('toCss', () => {
  it('rounds channels and keeps partial transparency', () => {
    expect(toCss(rgb(10.4, 20.6, 30))).toBe('rgb(10, 21, 30)')
    expect(toCss(rgb(0, 0, 0, 0.5))).toBe('rgba(0, 0, 0, 0.5)')
  })
})

describe('invertLightness', () => {
  it('turns black into white and dark gray into light gray', () => {
    expect(invertLightness(rgb(0, 0, 0))).toEqual(rgb(255, 255, 255))
    expect(invertLightness(rgb(34, 34, 34))).toEqual(rgb(221, 221, 221))
  })

  it('keeps the hue of colored text', () => {
    expect(invertLightness(rgb(0, 0, 128))).toEqual(rgb(127, 127, 255))
  })
})

describe('darkModeText', () => {
  it('lightens the dark text colors mail clients write', () => {
    expect(toCss(darkModeText(rgb(0, 0, 0)))).toBe('rgb(255, 255, 255)')
    expect(toCss(darkModeText(rgb(34, 34, 34)))).toBe('rgb(221, 221, 221)')
  })

  it('lightens pure blue, which flipping alone leaves unchanged', () => {
    const blue = rgb(0, 0, 255)
    const lighter = darkModeText(blue)
    expect(contrast(lighter, DARK_SURFACE)).toBeGreaterThanOrEqual(3)
    expect(lighter.b).toBe(255)
  })

  it('leaves readable colors alone', () => {
    expect(darkModeText(rgb(255, 255, 255))).toBeNull()
    expect(darkModeText(rgb(255, 0, 0))).toBeNull()
    expect(darkModeText(rgb(124, 124, 124))).toBeNull()
  })

  it('keeps black text on a mid gray background it already reads on', () => {
    expect(darkModeText(rgb(0, 0, 0), rgb(153, 153, 153))).toBeNull()
  })

  it('lightens black text whose light background turns dark', () => {
    const yellow = darkModeBackground(rgb(255, 255, 0))
    const text = darkModeText(rgb(0, 0, 0), yellow)
    expect(contrast(text, yellow)).toBeGreaterThanOrEqual(3)
  })

  it('ignores fully transparent colors', () => {
    expect(darkModeText(rgb(0, 0, 0, 0))).toBeNull()
  })
})

describe('darkModeBackground', () => {
  it('darkens white and pale backgrounds', () => {
    expect(toCss(darkModeBackground(rgb(255, 255, 255)))).toBe('rgb(0, 0, 0)')
    const cream = darkModeBackground(rgb(255, 255, 230))
    expect(contrast(cream, rgb(255, 255, 255))).toBeGreaterThan(4.5)
  })

  it('darkens pure yellow, which flipping alone leaves unchanged', () => {
    const yellow = rgb(255, 255, 0)
    expect(contrast(darkModeBackground(yellow), DARK_SURFACE)).toBeLessThan(
      contrast(yellow, DARK_SURFACE),
    )
  })

  it('leaves dark and mid-tone backgrounds alone', () => {
    expect(darkModeBackground(rgb(30, 30, 30))).toBeNull()
    expect(darkModeBackground(rgb(153, 153, 153))).toBeNull()
  })

  it('ignores the transparent default', () => {
    expect(darkModeBackground(rgb(0, 0, 0, 0))).toBeNull()
  })
})
