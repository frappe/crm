/**
 * Merge script-contributed tabs into a page's built-in tab list.
 *
 * Built-in tabs always keep their order and identity. A script tab whose `name`
 * matches a built-in tab patches that tab in place (so a script can relabel or
 * re-icon `Emails` without redefining it); anything else is appended.
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
  const seen = new Map(merged.map((tab, index) => [tab.name, index]))

  for (const tab of extra) {
    if (!tab || typeof tab !== 'object') continue
    if (!tab.name || typeof tab.name !== 'string') continue

    if (seen.has(tab.name)) {
      const index = seen.get(tab.name)
      merged[index] = { ...merged[index], ...tab }
      continue
    }

    seen.set(tab.name, merged.length)
    merged.push({ ...tab })
  }

  return merged
}

/**
 * Apply each tab's optional `condition()` guard.
 *
 * A tab with no `condition` is always kept. A `condition` that throws is
 * treated as false so one bad script tab cannot blank the whole tab bar.
 *
 * @param {Array} tabs
 * @returns {Array}
 */
export function filterVisibleTabs(tabs = []) {
  if (!Array.isArray(tabs)) return []

  return tabs.filter((tab) => {
    if (!tab || typeof tab.condition !== 'function') return true
    try {
      return Boolean(tab.condition())
    } catch (error) {
      console.error(`CRM: tab "${tab.name}" condition threw`, error)
      return false
    }
  })
}
