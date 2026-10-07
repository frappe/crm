const DARKEST_READABLE_TEXT = 0.14
const LIGHTEST_DARK_MODE_BACKGROUND = 0.4

export function parseRgb(value) {
  const match = value?.match(
    /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/,
  )
  if (!match) return null
  const [, r, g, b, a = '1'] = match
  return { r: +r, g: +g, b: +b, a: +a }
}

export function luminance({ r, g, b }) {
  const linear = (channel) => {
    const c = channel / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
}

// Shifting every channel by the same amount keeps hue and saturation, and this
// shift moves the lightness from L to 1 - L: black turns white, navy turns light blue.
export function invertLightness({ r, g, b, a }) {
  const shift = 255 - Math.max(r, g, b) - Math.min(r, g, b)
  const channels = [r, g, b].map((c) => c + shift).join(', ')
  return a < 1 ? `rgba(${channels}, ${a})` : `rgb(${channels})`
}

export function isUnreadableOnDark(color) {
  return color.a > 0 && luminance(color) < DARKEST_READABLE_TEXT
}

export function isTooLightForDark(background) {
  return (
    background.a > 0 && luminance(background) > LIGHTEST_DARK_MODE_BACKGROUND
  )
}
