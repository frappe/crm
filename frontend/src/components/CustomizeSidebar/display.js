import { builtInPage, DOCTYPE_ICON } from '@/utils/navigation'
import { editor } from './editor'
import { find, isAdded } from './rows'

/** A blank label shows the one below it. */
export function titleOf(row) {
  const label = row.label?.trim() || find(editor.below, row.key)?.label
  return label ? __(label) : row.link_to || ''
}

/** A lucide name, or a built-in page's own icon component. Sections have none. */
export function iconOf(row) {
  if (row.type === 'Section') return null
  return row.icon || builtInPage(row)?.icon || DOCTYPE_ICON
}

export function originOf(row) {
  if (row.key.startsWith('user:')) return __('Added by you')
  if (row.key.startsWith('site:')) return __('Added for everyone')
  return row.type === 'Section' ? __('Standard section') : __('Built-in page')
}

/** Public Views and Pinned Views: standard sections that fill themselves from saved views. */
export function fillsItself(row) {
  return row.type === 'Section' && !isAdded(row.key)
}
