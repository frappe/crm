// Publishing runs only through the Meta connection: Facebook pages and their
// linked Instagram business accounts.
export const SOCIAL_PLATFORM_COLORS = {
  Facebook: '#1877F2',
  Instagram: '#E4405F',
}

export function platformColor(platform) {
  return SOCIAL_PLATFORM_COLORS[platform] || '#6b7280'
}

export function platformInitial(platform) {
  return (platform || '?')[0]
}
