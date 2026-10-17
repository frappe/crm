import { markRaw, toRaw } from 'vue'

/**
 * Merge script-contributed tabs into a page's built-in tab list.
 *
 * Built-in tabs always keep their order and identity. A script tab whose `name`
 * matches a built-in tab, ignoring case, patches that tab in place (so a script
 * can relabel, re-icon or `hide` `Emails` without redefining it); the patched
 * tab keeps its own `name` and `value`. Anything else is appended.
 *
 * An appended tab without a `value` gets a slug of its `name`, the key the tab
 * bar and the URL hash select tabs by. A tab whose value is empty or already
 * taken by another tab is skipped with a warning, so no two tabs share a value.
 *
 * Components are marked raw so a reactive `document.tabs` never proxies them.
 *
 * Returns a NEW array — never mutates either input.
 *
 * @param {Array} baseTabs   tabs declared by the page
 * @param {Array} scriptTabs tabs pushed by a CRM Form Script (`this.tabs`)
 * @returns {Array}
 */
export function mergeFormTabs(baseTabs = [], scriptTabs = []) {
  const base = Array.isArray(baseTabs) ? baseTabs : []
  const extra = Array.isArray(scriptTabs) ? scriptTabs : []

  const merged = base.map((tab) => ({ ...tab }))
  const byName = new Map(merged.map((tab, index) => [nameKey(tab.name), index]))
  const values = new Set(merged.map((tab) => tab.value))

  for (const tab of extra) {
    if (!tab || typeof tab !== 'object') continue
    if (!tab.name || typeof tab.name !== 'string') continue

    const patch = { ...tab }
    if (patch.component) patch.component = markRaw(toRaw(patch.component))

    const key = nameKey(tab.name)
    if (byName.has(key)) {
      const index = byName.get(key)
      const { name, value } = merged[index]
      merged[index] = { ...merged[index], ...patch, name, value }
      continue
    }

    const value = patch.value ?? slugifyTabName(tab.name)
    if (!value || values.has(value)) {
      console.warn(
        `CRM: tab "${tab.name}" skipped, its value "${value}" is empty or already used`,
      )
      continue
    }

    byName.set(key, merged.length)
    values.add(value)
    merged.push({ ...patch, value })
  }

  return merged
}

/**
 * Turn a tab name into a URL-safe value: trimmed, lowercased, whitespace runs
 * replaced by `-`, and anything but letters (any script), digits, `-` and `_`
 * dropped.
 *
 * @param {string} name
 * @returns {string}
 */
export function slugifyTabName(name) {
  return String(name)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\p{L}\p{N}_-]/gu, '')
}

function nameKey(name) {
  return typeof name === 'string' ? name.trim().toLowerCase() : name
}

/**
 * Apply each tab's `hide` flag and optional `condition()` guard.
 *
 * `hide` drops the tab outright and takes precedence over `condition`. It is
 * how a script removes a built-in tab: pushing `{ name: 'Comments', hide: true }`
 * patches the built-in tab through `mergeFormTabs()`, and it is filtered out
 * here. It may also be a function, evaluated like `condition`.
 *
 * A tab with neither is always kept. A `condition` that throws is treated as
 * false, a `hide` that throws as false too — a broken guard hides at most its
 * own tab and never blanks the tab bar. Malformed entries are dropped, so
 * whatever reaches the tab bar is renderable.
 *
 * @param {Array} tabs
 * @returns {Array}
 */
export function filterVisibleTabs(tabs = []) {
  if (!Array.isArray(tabs)) return []

  return tabs.filter((tab) => {
    if (!tab || typeof tab !== 'object') return false
    if (isHidden(tab)) return false
    if (typeof tab.condition !== 'function') return true
    try {
      return Boolean(tab.condition())
    } catch (error) {
      console.error(`CRM: tab "${tab.name}" condition threw`, error)
      return false
    }
  })
}

function isHidden(tab) {
  if (typeof tab.hide !== 'function') return Boolean(tab.hide)
  try {
    return Boolean(tab.hide())
  } catch (error) {
    console.error(`CRM: tab "${tab.name}" hide threw`, error)
    return false
  }
}

// Built-in tabs whose pane renders the email composer, in the order to fall back to.
const COMPOSER_TABS = ['emails', 'activity', 'comments']

/**
 * Pick the tab to open the email composer on: the active tab if its pane
 * renders the composer, else the first visible built-in tab that does.
 *
 * A tab a script hid is not in `tabs`, and one a script gave a `component`
 * renders that component instead of the composer, so neither qualifies.
 *
 * @param {Array} tabs        visible tabs, as returned by filterVisibleTabs()
 * @param {string} activeTab  value of the active tab
 * @returns {string|null} the tab's value, or null when no tab has a composer
 */
export function composerTab(tabs = [], activeTab) {
  const values = new Set(
    (Array.isArray(tabs) ? tabs : [])
      .filter((tab) => tab && !tab.component)
      .map((tab) => tab.value),
  )
  if (COMPOSER_TABS.includes(activeTab) && values.has(activeTab))
    return activeTab
  return COMPOSER_TABS.find((value) => values.has(value)) ?? null
}
