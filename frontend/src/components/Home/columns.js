import { recordTitle } from '@/utils/home'

// minmax(0, …) lets cells truncate instead of widening the table past the card
const fr = (n) => `minmax(0,${n}fr)`

// Column definitions shared by Home widgets; `type` picks the renderer in HomeCell.
export const homeColumns = {
  record: () => ({
    key: 'title',
    label: __('Name'),
    width: fr(3),
    getLabel: ({ row }) => recordTitle(row),
  }),
  status: () => ({
    key: 'status',
    label: __('Status'),
    type: 'status',
    width: fr(2),
  }),
  task: () => ({ key: 'title', label: __('Task'), width: fr(3) }),
  taskRecord: () => ({
    key: 'reference_title',
    label: __('Record'),
    width: fr(2),
    getLabel: ({ row }) => row.reference_title || row.reference_docname,
  }),
  taskStatus: () => ({
    key: 'status',
    label: __('Status'),
    type: 'taskStatus',
    width: '5.5rem',
  }),
  priority: () => ({
    key: 'priority',
    label: __('Priority'),
    type: 'priority',
    width: '5.5rem',
  }),
  dueDate: (overdue = false) => ({
    key: 'due_date',
    label: __('Due date'),
    type: 'dueDate',
    width: '9rem',
    overdue,
  }),
  user: (key, label) => ({ key, label, type: 'user', width: fr(2) }),
  timeAgo: (key, label) => ({
    key,
    label,
    type: 'timeAgo',
    width: '6rem',
  }),
}

const NUMERIC = ['Int', 'Float', 'Currency', 'Percent', 'Duration', 'Rating']
const FIXED_WIDTHS = {
  Check: '4rem',
  Int: '5rem',
  Float: '5rem',
  Percent: '5rem',
  Rating: '6rem',
  Time: '5rem',
  Duration: '6rem',
  Currency: '7rem',
  Date: '7rem',
  Datetime: '8rem',
}

export function fieldWidth({ fieldtype }) {
  return FIXED_WIDTHS[fieldtype] || fr(2)
}

// A column the user added from the widget's fields.
export function fieldColumn(field) {
  const column = {
    key: field.fieldname,
    label: field.label,
    fieldtype: field.fieldtype,
    options: field.options,
    width: fieldWidth(field),
    align: NUMERIC.includes(field.fieldtype) ? 'right' : 'left',
  }
  if (['creation', 'modified'].includes(field.fieldname))
    return { ...homeColumns.timeAgo(field.fieldname, field.label), ...column }
  if (field.fieldtype === 'Link' && field.options === 'User')
    return { ...column, type: 'user' }
  return { ...column, type: 'field' }
}

// Saved columns override the widget's defaults; keys no longer available are skipped.
export function resolveColumns(defaults, saved, fields = {}) {
  if (!saved) return defaults
  return saved.flatMap(({ key, label, width }) => {
    const base = baseColumn(key, defaults, fields)
    if (!base) return []
    return [
      {
        ...base,
        label: label ?? base.label,
        width: cssWidth(width) ?? base.width,
      },
    ]
  })
}

// Only what differs from a column's default is stored.
export function toSavedColumns(columns, defaults, fields = {}) {
  return columns.map(({ key, label, width }) => {
    const base = baseColumn(key, defaults, fields) || {}
    const column = { key }
    if (label && label !== base.label) column.label = label
    if (width && width !== base.width) column.width = width
    return column
  })
}

export function keepAvailable(saved, defaults, fields) {
  return saved.filter(({ key }) => baseColumn(key, defaults, fields))
}

function baseColumn(key, defaults, fields) {
  const column = defaults.find((column) => column.key === key)
  if (column) return column
  return fields[key] && fieldColumn(fields[key])
}

// ColumnSettings documents bare numbers as widths; the grid needs a unit.
function cssWidth(width) {
  if (!width) return null
  return /^\d+(\.\d+)?$/.test(width) ? fr(width) : width
}
