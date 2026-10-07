const WHITE = { r: 255, g: 255, b: 255, a: 1 }
const BLACK = { r: 0, g: 0, b: 0, a: 1 }
// frappe-ui's dark surface-elevation-1 (darkMode/gray/900), the email card
export const DARK_SURFACE = { r: 31, g: 31, b: 31, a: 1 }

const MIN_TEXT_CONTRAST = 3
const LIGHT_BACKGROUND = 0.4
const DARKENED_BACKGROUND = 0.1

export function parseRgb(value) {
  const match = value?.match(
    /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/,
  )
  if (!match) return null
  const [, r, g, b, a = '1'] = match
  return { r: +r, g: +g, b: +b, a: +a }
}

export function toCss({ r, g, b, a }) {
  const channels = [r, g, b].map(Math.round).join(', ')
  return a < 1 ? `rgba(${channels}, ${a})` : `rgb(${channels})`
}

export function luminance({ r, g, b }) {
  const linear = (channel) => {
    const c = channel / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)
}

export function contrast(a, b) {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

export function blend(top, bottom) {
  const mix = (channel) => top[channel] * top.a + bottom[channel] * (1 - top.a)
  return { r: mix('r'), g: mix('g'), b: mix('b'), a: 1 }
}

// Shifting every channel by the same amount keeps hue and saturation, and this
// shift moves the lightness from L to 1 - L: black turns white, navy turns light blue.
export function invertLightness({ r, g, b, a }) {
  const shift = 255 - Math.max(r, g, b) - Math.min(r, g, b)
  return { r: r + shift, g: g + shift, b: b + shift, a }
}

function mixUntil(color, target, isGoodEnough) {
  for (let step = 0; step <= 10; step++) {
    const amount = step / 10
    const mixed = { ...color }
    for (const channel of ['r', 'g', 'b']) {
      mixed[channel] =
        color[channel] + (target[channel] - color[channel]) * amount
    }
    if (isGoodEnough(mixed)) return mixed
  }
  return { ...target, a: color.a }
}

export function darkModeBackground(background) {
  if (background.a === 0) return null
  if (luminance(background) <= LIGHT_BACKGROUND) return null
  return mixUntil(
    invertLightness(background),
    BLACK,
    (c) => luminance(c) <= DARKENED_BACKGROUND,
  )
}

export function darkModeText(color, background = DARK_SURFACE) {
  if (color.a === 0) return null
  const before = contrast(color, background)
  if (before >= MIN_TEXT_CONTRAST) return null
  const lighter = mixUntil(
    invertLightness(color),
    WHITE,
    (c) => contrast(c, background) >= MIN_TEXT_CONTRAST,
  )
  return contrast(lighter, background) > before ? lighter : null
}
