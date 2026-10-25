import { markRaw, toRaw } from 'vue'

/**
 * Merge a form script's `this.tabs` into a page's built-in tabs, without
 * mutating either, and return the visible ones. A script tab named like a
 * built-in one (ignoring case) patches it in place; any other tab with a
 * `component` is appended.
 */
export function mergeFormTabs(baseTabs, scriptTabs = []) {
  const merged = baseTabs.map((tab) => ({ ...tab }))
  const byName = new Map(
    merged.map((tab, index) => [tab.name.toLowerCase(), index]),
  )
  const values = new Set(merged.map((tab) => tab.value))

  for (const tab of scriptTabs) {
    if (typeof tab?.name !== 'string' || !tab.name.trim()) {
      console.warn('CRM: tab skipped, its name must be a non-empty string')
      continue
    }

    const patch = { ...tab }
    // keep a reactive document.tabs from proxying components
    for (const prop of ['component', 'iconLeft']) {
      if (patch[prop]) patch[prop] = markRaw(toRaw(patch[prop]))
    }

    const key = tab.name.trim().toLowerCase()
    if (byName.has(key)) {
      const index = byName.get(key)
      const builtIn = merged[index]
      merged[index] = {
        ...builtIn,
        ...patch,
        name: builtIn.name,
        value: builtIn.value,
        condition: both(builtIn.condition, patch.condition),
      }
      continue
    }

    const value = patch.value ?? slugifyTabName(tab.name)
    if (!patch.component || !value || values.has(value)) {
      console.warn(
        `CRM: tab "${tab.name}" skipped, it needs a component and a unique value`,
      )
      continue
    }

    byName.set(key, merged.length)
    values.add(value)
    merged.push({ label: tab.name, ...patch, value })
  }

  return merged.filter((tab) => {
    // a broken script guard hides its own tab, not the whole tab bar
    try {
      return tab.condition == null || isMet(tab.condition)
    } catch (error) {
      console.error(`CRM: tab "${tab.name}" visibility check failed`, error)
      return false
    }
  })
}

// a condition is a boolean or a function returning one
function isMet(condition) {
  return Boolean(typeof condition === 'function' ? condition() : condition)
}

function both(a, b) {
  if (a == null || b == null) return a ?? b
  return () => isMet(a) && isMet(b)
}

// URL-safe tab value; keeps letters of any script
function slugifyTabName(name) {
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\p{L}\p{N}_-]/gu, '')
}

// Built-in tabs whose pane renders the email composer, in fallback order.
const COMPOSER_TABS = ['emails', 'activity', 'comments']

// The tab to open the email composer on: the active one if it has a composer,
// else the first visible built-in tab that does. Null when none has one.
export function composerTab(tabs, activeTab) {
  const values = new Set(
    tabs.filter((tab) => !tab.component).map((tab) => tab.value),
  )
  if (COMPOSER_TABS.includes(activeTab) && values.has(activeTab))
    return activeTab
  return COMPOSER_TABS.find((value) => values.has(value)) ?? null
}
