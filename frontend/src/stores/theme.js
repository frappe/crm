import { useStorage } from '@vueuse/core'

export const theme = useStorage('theme', 'light')

export function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme')
  theme.value = currentTheme === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
}

export function setTheme(value) {
  theme.value = value || theme.value
  if (['light', 'dark'].includes(theme.value)) {
    document.documentElement.setAttribute('data-theme', theme.value)
  }
}
