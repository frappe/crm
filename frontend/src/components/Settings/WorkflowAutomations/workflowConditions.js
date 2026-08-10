/**
 * Filter rows <-> the Python expression a step condition is stored as.
 *
 * The engine evaluates `step_condition` with `safe_eval`, so the expression stays the stored
 * form and the filter rows are only a way to write one. Anything this module can't parse back
 * is still a perfectly good condition — the editor just falls back to editing it as text.
 *
 * `safe_eval` exposes no builtins, so the generated code sticks to comparisons, `in` and `or`.
 */

const NUMERIC_FIELDTYPES = ['Int', 'Float', 'Currency', 'Percent']
const COMPARISONS = ['==', '!=', '>=', '<=', '>', '<']
const OPERATOR_TO_PYTHON = { '=': '==', '!=': '!=' }

export function toExpression(filters, fields = []) {
  const clauses = (filters || [])
    .filter((filter) => filter[0] && filter[1])
    .map((filter) => clauseFor(filter, fields))
    .filter(Boolean)
  return clauses.join(' and ')
}

export function toFilters(expression) {
  const text = String(expression || '').trim()
  if (!text) return []
  const parsed = text.split(' and ').map((clause) => parseClause(clause.trim()))
  return parsed.every(Boolean) ? parsed : null
}

/** Whether the filter UI can represent this expression without losing anything. */
export function isFilterExpression(expression) {
  return toFilters(expression) !== null
}

function clauseFor(filter, fields) {
  const [fieldname, operator, value] = filter
  if (operator === 'is') return presenceClause(fieldname, value)
  if (operator === 'like' || operator === 'not like')
    return containsClause(fieldname, operator, value)
  if (operator === 'in' || operator === 'not in')
    return listClause(fieldname, operator, value, fields)
  const comparison = OPERATOR_TO_PYTHON[operator] || operator
  if (!COMPARISONS.includes(comparison)) return ''
  return `doc.${fieldname} ${comparison} ${literal(value, fieldname, fields)}`
}

function presenceClause(fieldname, value) {
  const comparison = value === 'not set' ? '==' : '!='
  return `(doc.${fieldname} or "") ${comparison} ""`
}

function containsClause(fieldname, operator, value) {
  const needle = String(value ?? '')
    .replace(/%/g, '')
    .toLowerCase()
  const membership = operator === 'like' ? 'in' : 'not in'
  return `${quote(needle)} ${membership} (doc.${fieldname} or "").lower()`
}

function listClause(fieldname, operator, value, fields) {
  const items = (Array.isArray(value) ? value : splitValues(value)).map(
    (item) => literal(item, fieldname, fields),
  )
  return `doc.${fieldname} ${operator} [${items.join(', ')}]`
}

function literal(value, fieldname, fields) {
  if (typeof value === 'number') return String(value)
  const text = String(value ?? '')
  const field = fields.find((item) => item.fieldname === fieldname)
  const numeric =
    NUMERIC_FIELDTYPES.includes(field?.fieldtype) ||
    field?.fieldtype === 'Check'
  if (numeric && text !== '' && !Number.isNaN(Number(text))) return text
  return quote(text)
}

function quote(text) {
  return `"${String(text).replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function splitValues(value) {
  return String(value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

// --- parsing -------------------------------------------------------------
const PRESENCE = /^\(doc\.(\w+) or ""\) (==|!=) ""$/
const CONTAINS = /^["'](.*)["'] (not in|in) \(doc\.(\w+) or ""\)\.lower\(\)$/
const MEMBERSHIP = /^doc\.(\w+) (not in|in) \[(.*)\]$/
const COMPARISON = /^doc\.(\w+) (==|!=|>=|<=|>|<) (.+)$/

function parseClause(clause) {
  return (
    parsePresence(clause) ||
    parseContains(clause) ||
    parseMembership(clause) ||
    parseComparison(clause)
  )
}

function parsePresence(clause) {
  const match = clause.match(PRESENCE)
  if (!match) return null
  return [match[1], 'is', match[2] === '==' ? 'not set' : 'set']
}

function parseContains(clause) {
  const match = clause.match(CONTAINS)
  if (!match) return null
  return [match[3], match[2] === 'in' ? 'like' : 'not like', unquote(match[1])]
}

function parseMembership(clause) {
  const match = clause.match(MEMBERSHIP)
  if (!match) return null
  const items = match[3]
    .split(',')
    .map((item) => parseLiteral(item.trim()))
    .filter((item) => item !== '')
  return [match[1], match[2], items]
}

function parseComparison(clause) {
  const match = clause.match(COMPARISON)
  if (!match) return null
  const operator = match[2] === '==' ? '=' : match[2]
  return [match[1], operator, parseLiteral(match[3].trim())]
}

/** Conditions written by hand or seeded from Python use either quote style. */
function parseLiteral(text) {
  if (/^".*"$/.test(text) || /^'.*'$/.test(text))
    return unquote(text.slice(1, -1))
  if (text === '') return ''
  return Number.isNaN(Number(text)) ? text : Number(text)
}

function unquote(text) {
  return text.replace(/\\"/g, '"').replace(/\\\\/g, '\\')
}
