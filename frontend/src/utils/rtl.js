/** Languages Frappe treats as RTL. Keep in sync with frappe.utils.is_rtl. */
export const RTL_LANGUAGES = ['ar', 'he', 'fa', 'ps']

export function normalizeLanguage(lang) {
  if (!lang || typeof lang !== 'string') return ''
  return lang.trim().toLowerCase().split(/[-_]/)[0]
}

export function isRtlLanguage(lang) {
  return RTL_LANGUAGES.includes(normalizeLanguage(lang))
}

export function resolveBootLanguage(boot = globalThis) {
  return boot?.lang || boot?.sysdefaults?.language || boot?.sysdefaults?.lang || ''
}

export function applyDocumentDirection(
  lang,
  root = typeof document !== 'undefined' ? document.documentElement : null,
) {
  const resolved = normalizeLanguage(lang) || 'en'
  const dir = isRtlLanguage(resolved) ? 'rtl' : 'ltr'
  if (root) {
    root.lang = resolved
    root.setAttribute('dir', dir)
  }
  return { lang: resolved, dir }
}
