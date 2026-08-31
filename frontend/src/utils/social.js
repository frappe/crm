export const SOCIAL_PLATFORM_COLORS = {
  Facebook: '#1877F2',
  Instagram: '#E4405F',
  LinkedIn: '#0A66C2',
  TikTok: '#111111',
  YouTube: '#FF0000',
  Pinterest: '#BD081C',
  'Google Business Profile': '#4285F4',
  Threads: '#111111',
  Bluesky: '#0285FF',
  X: '#111111',
}

export const SOCIAL_PLATFORMS = Object.keys(SOCIAL_PLATFORM_COLORS)

export function platformColor(platform) {
  return SOCIAL_PLATFORM_COLORS[platform] || '#6b7280'
}

// short badge letters for post chips (initials where no icon is available)
export function platformInitial(platform) {
  return (
    {
      'Google Business Profile': 'G',
      X: '𝕏',
    }[platform] || (platform || '?')[0]
  )
}
