import { call } from 'frappe-ui'

const SCORE = {
  prefix: 1000,
  word: 850,
  substring: 700,
  subsequence: 400,
}

function normalize(value) {
  return String(value || '')
    .trim()
    .toLocaleLowerCase()
}

function wordBoundaryIndex(text, term) {
  const match = text.match(new RegExp(`(?:^|\\s)${escapeRegExp(term)}`))
  return match?.index ?? -1
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function subsequenceGap(text, term) {
  let lastIndex = -1
  let gap = 0
  for (const character of term) {
    const index = text.indexOf(character, lastIndex + 1)
    if (index < 0) return -1
    gap += index - lastIndex - 1
    lastIndex = index
  }
  return gap
}

export function fuzzyScore(value, query) {
  const text = normalize(value)
  const term = normalize(query)
  if (!term) return 0
  if (text.startsWith(term)) return SCORE.prefix - (text.length - term.length)
  const wordIndex = wordBoundaryIndex(text, term)
  if (wordIndex >= 0) return SCORE.word - wordIndex
  const substringIndex = text.indexOf(term)
  if (substringIndex >= 0) return SCORE.substring - substringIndex
  const gap = subsequenceGap(text, term)
  return gap < 0 ? -1 : SCORE.subsequence - gap
}

export function scoreCommand(command, query) {
  if (command.rank != null) return command.rank
  const titleScore = fuzzyScore(command.title, query)
  const keywordScore = fuzzyScore(command.keywords, query) * 0.75
  return Math.max(titleScore, keywordScore) * (command.weight ?? 1)
}

export function groupCommands(commands, query = '') {
  const groups = new Map()
  for (const command of rankedCommands(commands, query)) {
    const group = command.group || ''
    if (!groups.has(group)) groups.set(group, [])
    groups.get(group).push(command)
  }
  return [...groups].map(([title, items]) => ({ title, items }))
}

export function checkedFirst(commands = []) {
  return [
    ...commands.filter((command) => command.checked),
    ...commands.filter((command) => !command.checked),
  ]
}

export function flattenCommandActions(actions = []) {
  return actions.flatMap((action) => action.options || action.items || action)
}

export const FILTERABLE_FIELDTYPES = ['Check', 'Select', 'Link']

export async function commandFilterOptions(filter) {
  if (filter.fieldtype === 'Check') {
    return [
      { label: 'Yes', value: '1' },
      { label: 'No', value: '0' },
    ]
  }
  if (filter.fieldtype === 'Link') return linkOptions(filter.options)
  return selectOptions(filter.options)
}

// `options` on a Link quick filter is the target doctype, not a list of values.
async function linkOptions(doctype) {
  if (!doctype) return []
  const results = await call('frappe.desk.search.search_link', {
    txt: '',
    doctype,
  })
  return results.map((result) => ({
    label: result.label || result.value,
    value: result.value,
  }))
}

function selectOptions(options) {
  const values = Array.isArray(options)
    ? options
    : String(options || '').split('\n')
  return values
    .map((option) =>
      typeof option === 'object' ? option : { label: option, value: option },
    )
    .filter((option) => option.value)
}

function rankedCommands(commands, query) {
  const typed = Boolean(normalize(query))
  return commands
    .filter((command) => typed || !command.hideWhenEmpty)
    .map((command, index) => ({
      command,
      index,
      score: scoreCommand(command, query),
    }))
    .filter(({ score }) => score >= 0)
    .sort((a, b) => b.score - a.score || a.index - b.index)
    .map(({ command }) => command)
}
