/**
 * Filter rows <-> the Python expression a step condition is stored as.
 *
 * The engine evaluates `step_condition` with `safe_eval`, so the expression stays the stored
 * form and the filter rows are only a way to write one. Anything this module can't parse back
 * is still a perfectly good condition - the editor just falls back to editing it as text.
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

/** A one-line reading of a condition, for canvas nodes and the read-only view. */
export function summarizeCondition(expression) {
  const filters = toFilters(expression)
  if (!filters) return String(expression || '')
  return filters.map(describeFilter).join(__(' and '))
}

const PHRASES = {
  '=': (field, value) => __('{0} is {1}', [field, value]),
  '!=': (field, value) => __('{0} is not {1}', [field, value]),
  in: (field, value) => __('{0} is one of {1}', [field, value]),
  'not in': (field, value) => __('{0} is none of {1}', [field, value]),
  like: (field, value) => __('{0} contains {1}', [field, value]),
  'not like': (field, value) => __('{0} does not contain {1}', [field, value]),
}

function describeFilter([fieldname, operator, value]) {
  const field = prettyField(fieldname)
  if (operator === 'is')
    return value === 'set'
      ? __('{0} is set', [field])
      : __('{0} is empty', [field])
  const phrase = PHRASES[operator]
  const text = Array.isArray(value) ? value.join(', ') : String(value ?? '')
  return phrase ? phrase(field, text) : `${field} ${operator} ${text}`
}

function prettyField(fieldname) {
  const words = String(fieldname || '').replace(/_/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
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
// Deliberately strict: a clause has to be a field, an operator and plain literals. Anything
// looser would let a hand-written expression half-match, and rewriting it from the filter UI
// would silently change what the step does.
const LITERAL = `"[^"]*"|'[^']*'|-?\\d+(?:\\.\\d+)?`
const PRESENCE = /^\(doc\.(\w+) or ""\) (==|!=) ""$/
const CONTAINS =
  /^"([^"]*)" (not in|in) \(doc\.(\w+) or ""\)\.lower\(\)$|^'([^']*)' (not in|in) \(doc\.(\w+) or ""\)\.lower\(\)$/
const MEMBERSHIP = new RegExp(
  `^doc\\.(\\w+) (not in|in) \\[((?:${LITERAL})(?:, *(?:${LITERAL}))*)?\\]$`,
)
const COMPARISON = new RegExp(`^doc\\.(\\w+) (==|!=|>=|<=|>|<) (${LITERAL})$`)

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
  const [value, operator, fieldname] =
    match[1] === undefined
      ? [match[4], match[5], match[6]]
      : [match[1], match[2], match[3]]
  return [fieldname, operator === 'in' ? 'like' : 'not like', unquote(value)]
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
