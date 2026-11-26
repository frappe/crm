import { toolLabel } from './flowEvents'

const CODE_TOOLS = new Set(['execute'])

/**
 * What one call waiting for approval will do, as rows of label and value: the fields
 * a create or update sets, the records an update or delete touches, or any other
 * tool's arguments. Code is not summed up: its description stands for it.
 */
export function summarizeCall(call) {
  const args = call.args || call.arguments || {}
  const title = String(call.prompt || '').split('\n')[0] || toolLabel(call)
  if (CODE_TOOLS.has(call.name))
    return { title, code: true, description: args.description || '', rows: [] }
  return { title, code: false, description: '', rows: rowsFor(call.name, args) }
}

function rowsFor(name, args) {
  if (name === 'create') return createRows(args.records || [])
  if (name === 'update')
    return [recordsRow(args.names), ...fieldRows(args.values || {})]
  if (name === 'delete') return [recordsRow(args.names)]
  return fieldRows(args)
}

function createRows(records) {
  if (records.length === 1) return fieldRows(records[0])
  return records.map((record, index) => ({
    label: `#${index + 1}`,
    value: Object.entries(record)
      .map(([field, value]) => `${fieldLabel(field)}: ${plainValue(value)}`)
      .join(' · '),
  }))
}

function recordsRow(names = []) {
  return { label: __('Records'), value: names.join(', ') }
}

function fieldRows(values) {
  return Object.entries(values).map(([field, value]) => ({
    label: fieldLabel(field),
    value: plainValue(value),
  }))
}

export function fieldLabel(field) {
  const words = String(field).replace(/_/g, ' ').trim()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

/** A value as text: rich text loses its tags, nested values read as JSON. */
export function plainValue(value) {
  if (value == null || value === '') return '—'
  if (Array.isArray(value) && value.every((item) => typeof item !== 'object'))
    return value.join(', ')
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
