import {
  parseRgb,
  invertLightness,
  isUnreadableOnDark,
  isTooLightForDark,
} from '@/utils/emailColors'

describe('parseRgb', () => {
  it('reads computed rgb and rgba values', () => {
    expect(parseRgb('rgb(34, 34, 34)')).toEqual({ r: 34, g: 34, b: 34, a: 1 })
    expect(parseRgb('rgba(0, 0, 0, 0)')).toEqual({ r: 0, g: 0, b: 0, a: 0 })
  })

  it('returns null for anything else', () => {
    expect(parseRgb('black')).toBeNull()
    expect(parseRgb('')).toBeNull()
    expect(parseRgb(undefined)).toBeNull()
  })
})

describe('invertLightness', () => {
  it('turns black into white and dark gray into light gray', () => {
    expect(invertLightness({ r: 0, g: 0, b: 0, a: 1 })).toBe(
      'rgb(255, 255, 255)',
    )
    expect(invertLightness({ r: 34, g: 34, b: 34, a: 1 })).toBe(
      'rgb(221, 221, 221)',
    )
  })

  it('keeps the hue of colored text', () => {
    expect(invertLightness({ r: 0, g: 0, b: 128, a: 1 })).toBe(
      'rgb(127, 127, 255)',
    )
  })

  it('keeps partial transparency', () => {
    expect(invertLightness({ r: 0, g: 0, b: 0, a: 0.5 })).toBe(
      'rgba(255, 255, 255, 0.5)',
    )
  })
})

describe('isUnreadableOnDark', () => {
  it('flags the dark text colors mail clients write', () => {
    expect(isUnreadableOnDark(parseRgb('rgb(0, 0, 0)'))).toBe(true)
    expect(isUnreadableOnDark(parseRgb('rgb(34, 34, 34)'))).toBe(true)
    expect(isUnreadableOnDark(parseRgb('rgb(0, 0, 128)'))).toBe(true)
  })

  it('leaves light and bright colors alone', () => {
    expect(isUnreadableOnDark(parseRgb('rgb(255, 255, 255)'))).toBe(false)
    expect(isUnreadableOnDark(parseRgb('rgb(255, 0, 0)'))).toBe(false)
  })

  it('ignores fully transparent colors', () => {
    expect(isUnreadableOnDark(parseRgb('rgba(0, 0, 0, 0)'))).toBe(false)
  })
})

describe('isTooLightForDark', () => {
  it('flags white and pale backgrounds', () => {
    expect(isTooLightForDark(parseRgb('rgb(255, 255, 255)'))).toBe(true)
    expect(isTooLightForDark(parseRgb('rgb(255, 255, 0)'))).toBe(true)
  })

  it('leaves dark and mid-tone backgrounds alone', () => {
    expect(isTooLightForDark(parseRgb('rgb(30, 30, 30)'))).toBe(false)
    expect(isTooLightForDark(parseRgb('rgb(74, 144, 226)'))).toBe(false)
  })

  it('ignores the transparent default', () => {
    expect(isTooLightForDark(parseRgb('rgba(0, 0, 0, 0)'))).toBe(false)
  })
})
