// The Customize sidebar dialog's rows, modelled on desk v2's navigation editor.
// Pure: every edit returns the next list or a refusal string, and nothing throws.
// The list is flat and keeps the order the sidebar draws: main list items first,
// then each section followed by its items.

const MARKERS = ['no_access', 'hidden_by']
const INHERITED_FIELDS = ['label', 'icon', 'collapsible', 'keep_closed']

export function isOwn(key, scope) {
  return key.startsWith(`${scope}:`)
}

export function isAdded(key) {
  return key.startsWith('site:') || key.startsWith('user:')
}

/** A section a layer added; only these hold items. Public and Pinned Views fill themselves. */
export function isCustomSection(row) {
  return row?.type === 'Section' && isAdded(row.key)
}

/** A new own key: the scope, a colon and six base36 characters. */
export function newKey(scope) {
  const bytes = crypto.getRandomValues(new Uint8Array(6))
  return `${scope}:${Array.from(bytes, (byte) => (byte % 36).toString(36)).join('')}`
}

export function find(rows, key) {
  return rows.find((row) => row.key === key)
}

/** Main list items first, then each section followed by its items. */
export function ordered(rows) {
  const sections = rows.filter((row) => row.type === 'Section')
  const main = rows.filter((row) => row.type !== 'Section' && !row.parent_key)
  return [
    ...main,
    ...sections.flatMap((section) => [
      section,
      ...rows.filter((row) => row.parent_key === section.key),
    ]),
  ]
}

/** Whether the outline lists the row: hidden rows and the rows of a hidden section only with Show hidden. */
export function isListed(rows, row, showHidden) {
  if (showHidden) return true
  return !row.hidden && !find(rows, row.parent_key)?.hidden
}

/**
 * An inherited row takes only its label, icon and section flags. A cleared icon takes
 * the one below; a blank label stays blank, and the save keeps the label below.
 */
export function update(rows, key, fields, scope, below = []) {
  const row = find(rows, key)
  if (!row) return __('This row no longer exists.')
  const own = isOwn(key, scope)
  const allowed = own
    ? { ...fields }
    : Object.fromEntries(
        INHERITED_FIELDS.filter((field) => field in fields).map((field) => [
          field,
          fields[field],
        ]),
      )
  if (!own && 'icon' in allowed && !allowed.icon) {
    allowed.icon = find(below, key)?.icon ?? null
  }
  if ('collapsible' in allowed && !allowed.collapsible) allowed.keep_closed = 0
  return replace(rows, key, (current) => ({ ...current, ...allowed }))
}

/** Hide or show a row; Show also works on a row the site hid. */
export function toggleHidden(rows, key) {
  if (!find(rows, key)) return __('This row no longer exists.')
  return replace(rows, key, (row) => {
    const shown = { ...row, hidden: row.hidden ? 0 : 1 }
    delete shown.hidden_by
    return shown
  })
}

/** Put an item in a section a layer added, or in the main list with a blank parent. It lands last. */
export function nest(rows, key, parentKey) {
  const row = find(rows, key)
  if (!row) return __('This row no longer exists.')
  if (row.type === 'Section') return __('A section stays in the main list.')
  const refusal = parentRefusal(rows, parentKey)
  if (refusal) return refusal
  if ((row.parent_key || null) === (parentKey || null)) return rows
  const moved = { ...row, parent_key: parentKey || null }
  return ordered([...rows.filter((entry) => entry.key !== key), moved])
}

/** Swap a row with the next sibling the outline shows, in the same section and of the same kind. */
export function moveBy(rows, key, by, isShown = () => true) {
  const row = find(rows, key)
  if (!row) return rows
  const group = rows.filter((entry) => isSibling(entry, row))
  let to = group.indexOf(row) + by
  while (to >= 0 && to < group.length && !isShown(group[to])) to += by
  if (to < 0 || to >= group.length) return rows

  const rest = rows.filter((entry) => entry !== row)
  const at = rest.indexOf(group[to]) + (by > 0 ? 1 : 0)
  return ordered([...rest.slice(0, at), row, ...rest.slice(at)])
}

/**
 * A drop on an item puts the dragged item before it, in its section. A drop on a
 * section a layer added puts an item in it, last. A dragged section lands before
 * the section it is dropped on, or before the section of the item it is dropped on.
 */
export function drop(rows, key, onKey) {
  const dragged = find(rows, key)
  const target = find(rows, onKey)
  if (!dragged || !target || dragged === target) return rows

  if (dragged.type === 'Section') {
    const anchor =
      target.type === 'Section' ? target : find(rows, target.parent_key)
    if (!anchor) return __('Sections sit below the main list.')
    return placeBefore(rows, dragged, anchor)
  }
  if (target.type === 'Section') return nest(rows, key, target.key)
  return placeBefore(
    rows,
    { ...dragged, parent_key: target.parent_key },
    target,
  )
}

/** Add a row this layer owns: an item last in its section or the main list, a section before Public Views. */
export function add(rows, row, parentKey = null) {
  if (row.type === 'Section') {
    const at = rows.findIndex(
      (entry) => entry.type === 'Section' && !isAdded(entry.key),
    )
    const index = at < 0 ? rows.length : at
    return [...rows.slice(0, index), row, ...rows.slice(index)]
  }
  const refusal = parentRefusal(rows, parentKey)
  if (refusal) return refusal
  return ordered([...rows, { ...row, parent_key: parentKey || null }])
}

/** Delete a row this layer added; a deleted section's items go back to the main list. */
export function remove(rows, key, scope) {
  if (!find(rows, key)) return __('This row no longer exists.')
  if (!isOwn(key, scope)) {
    return __('Only a row you added can be deleted. Hide it instead.')
  }
  return ordered(
    rows
      .filter((row) => row.key !== key)
      .map((row) =>
        row.parent_key === key ? { ...row, parent_key: null } : row,
      ),
  )
}

/** Why a DocType cannot be added, or given to row `exceptKey`: a built-in page or another row opens it. */
export function doctypeRefusal(rows, doctype, builtInDoctypes, exceptKey) {
  if (builtInDoctypes[doctype]) {
    return __('{0} already opens {1}.', [__(builtInDoctypes[doctype]), doctype])
  }
  const present = rows.find(
    (row) =>
      row.key !== exceptKey &&
      row.link_type === 'DocType' &&
      row.link_to === doctype,
  )
  if (present) {
    return __('{0} is already in the sidebar, as {1}.', [
      doctype,
      present.label || doctype,
    ])
  }
  return null
}

/** The layer below as a draft: saving it stores nothing for this layer. */
export function resetToDefault(rows, below, scope) {
  const noAccess = new Set(
    rows.filter((row) => row.no_access).map((row) => row.key),
  )
  return below.map((row) => {
    const reset = { ...row }
    if (noAccess.has(row.key)) reset.no_access = 1
    if (scope === 'user' && row.hidden) reset.hidden_by = 'site'
    return reset
  })
}

/** Whether rows differ from the opened copy; markers and key order do not count. */
export function isChanged(opened, rows) {
  return canonical(opened) !== canonical(rows)
}

/** The rows as the save sends them: markers dropped. */
export function toPayload(rows) {
  return rows.map(unmarked)
}

function unmarked(row) {
  const copy = { ...row }
  for (const marker of MARKERS) delete copy[marker]
  return copy
}

function canonical(rows) {
  return JSON.stringify(
    rows.map((row) => {
      const plain = unmarked(row)
      return Object.keys(plain)
        .filter((field) => plain[field] !== undefined && plain[field] !== null)
        .sort()
        .map((field) => [field, plain[field]])
    }),
  )
}

function parentRefusal(rows, parentKey) {
  if (!parentKey) return null
  const parent = find(rows, parentKey)
  if (!parent) return __('That section no longer exists.')
  if (!isCustomSection(parent)) {
    return __(
      '{0} fills itself from saved views. Nothing can be added to it.',
      [__(parent.label)],
    )
  }
  return null
}

function isSibling(entry, row) {
  return (
    (entry.parent_key || null) === (row.parent_key || null) &&
    (entry.type === 'Section') === (row.type === 'Section')
  )
}

function placeBefore(rows, row, before) {
  const rest = rows.filter((entry) => entry.key !== row.key)
  const at = rest.findIndex((entry) => entry.key === before.key)
  return ordered([...rest.slice(0, at), row, ...rest.slice(at)])
}

function replace(rows, key, change) {
  return rows.map((row) => (row.key === key ? change(row) : row))
}
