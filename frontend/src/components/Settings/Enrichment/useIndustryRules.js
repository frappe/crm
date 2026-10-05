import { call } from 'frappe-ui'
import { useEnrichmentRules } from './useEnrichmentRules'

// Regexes (compiled verbatim, not escaped) and keywords with commas can't
// round-trip the box.
function isKeywordRow(row) {
  return Number(row.is_regex) !== 1 && !String(row.pattern).includes(',')
}

// Parsed on load too, so the box shows what a save would store and an untouched
// rule isn't edited.
function splitPatterns(patternRows) {
  const list = patternRows || []

  return {
    keywords: parseKeywords(
      list
        .filter(isKeywordRow)
        .map((row) => row.pattern)
        .join(', '),
    ).join(', '),
    hidden: list.filter((row) => !isKeywordRow(row)).map((row) => row.pattern),
  }
}

// Deduped case-insensitively since config._compile_pattern uses re.I; the first
// spelling wins.
function parseKeywords(text) {
  const seen = new Set()
  const keywords = []

  ;(text || '').split(',').forEach((part) => {
    const keyword = part.trim()
    if (!keyword) return

    const folded = keyword.toLowerCase()
    if (seen.has(folded)) return

    seen.add(folded)
    keywords.push(keyword)
  })

  return keywords
}

export function useIndustryRules() {
  const rules = useEnrichmentRules({
    ruleType: 'Industry',
    fields: ['industry'],
    buildRow,
    newRow,
    isRowChanged,
    validateRow,
    toInsert,
    toUpdate,
    clearErrors,
    messages: {
      insertError: __('Could not add industry rule'),
      updateError: __('Could not save industry rule'),
      deleteError: __('Could not delete industry rule'),
    },
  })

  function buildRow(rule, patternRows, held) {
    const { keywords, hidden } = splitPatterns(patternRows)

    return {
      industry: held ? held.industry : rule.industry || '',
      keywords: held ? held.keywords : keywords,
      // The CRM Industry is inserted on Save, before the rule that links it.
      newIndustry: held ? held.newIndustry : false,
      savedIndustry: rule.industry || '',
      savedKeywords: keywords,
      hidden,
      industryError: held ? held.industryError : '',
      keywordsError: held ? held.keywordsError : '',
    }
  }

  function newRow() {
    return {
      industry: '',
      keywords: '',
      newIndustry: false,
      savedIndustry: '',
      savedKeywords: '',
      hidden: [],
      industryError: '',
      keywordsError: '',
    }
  }

  function clearErrors(row) {
    row.industryError = ''
    row.keywordsError = ''
  }

  // Compared as Save would send it, so stray spaces or commas don't mark the
  // row dirty.
  function isRowChanged(row) {
    return (
      row.industry !== row.savedIndustry ||
      parseKeywords(row.keywords).join(', ') !== row.savedKeywords
    )
  }

  // Case-insensitive like the server's duplicate check.
  function industryTakenBy(industry, others) {
    const folded = industry.toLowerCase()

    return others.some(
      (other) => (other.industry || '').toLowerCase() === folded,
    )
  }

  function validateRow(row, others) {
    if (!row.industry) {
      row.industryError = __('Industry is required')
    } else if (industryTakenBy(row.industry, others)) {
      row.industryError = __('A rule for {0} already exists', [row.industry])
    }

    if (!parseKeywords(row.keywords).length) {
      row.keywordsError = __('At least one keyword is required')
    }

    return !row.industryError && !row.keywordsError
  }

  // Snaps the box to the stored form so the admin sees trimming and dedupe.
  function checkRow(row) {
    row.keywords = parseKeywords(row.keywords).join(', ')
    if (!row.name || isRowChanged(row)) {
      clearErrors(row)
      validateRow(
        row,
        rules.rows.value.filter((other) => other !== row && !other.removed),
      )
    }
  }

  function onIndustryChange(row, value) {
    row.industry = value || ''
    row.newIndustry = false
    row.industryError = ''
    row.serverError = ''
    checkRow(row)
  }

  // The CRM Industry is only inserted on Save, so abandoning the row leaves no
  // stray industry.
  function onIndustryCreate(row, value, close) {
    const industry = (value || '').trim()
    if (!industry) return
    close?.()

    row.industry = industry
    row.newIndustry = true
    row.industryError = ''
    row.serverError = ''
    checkRow(row)
  }

  function onKeywordsInput(row, value) {
    row.keywords = value
    row.keywordsError = ''
    row.serverError = ''
  }

  // DuplicateEntryError means the industry already exists (another row or
  // user), which is fine.
  async function ensureIndustry(row) {
    if (!row.newIndustry) return
    try {
      await call('frappe.client.insert', {
        doc: { doctype: 'CRM Industry', industry: row.industry },
      })
    } catch (err) {
      if (err?.exc_type !== 'DuplicateEntryError') throw err
    }
    row.newIndustry = false
  }

  async function toInsert(row) {
    await ensureIndustry(row)

    return {
      industry: row.industry,
      // Set explicitly: weight scales hits in extractors.py and an API insert
      // may skip the default.
      weight: 1,
      // Matches the seeded Industry rules: name, description, title and
      // headings, not body copy.
      match_scope: 'Headline',
      patterns: parseKeywords(row.keywords).map((keyword) => ({
        pattern: keyword,
        is_regex: 0,
      })),
    }
  }

  // weight is never sent, so an existing rule keeps its own.
  async function toUpdate(row, doc) {
    await ensureIndustry(row)

    const values = { industry: row.industry }

    const patternRows = doc.patterns || []
    // Reuse child rows so untouched keywords aren't dropped and re-created.
    const existing = new Map(
      patternRows.filter(isKeywordRow).map((entry) => [entry.pattern, entry]),
    )
    const pick = ({ name, pattern, is_regex }) => ({ name, pattern, is_regex })

    values.patterns = [
      ...parseKeywords(row.keywords).map((keyword) =>
        existing.has(keyword)
          ? pick(existing.get(keyword))
          : { pattern: keyword, is_regex: 0 },
      ),
      // Rows the box never owned go back as read, last, so typed keywords keep
      // their order.
      ...patternRows.filter((entry) => !isKeywordRow(entry)).map(pick),
    ]

    return values
  }

  function isRowBlank(row) {
    return !row.name && !row.industry && !row.keywords.trim()
  }

  return {
    ...rules,
    isRowBlank,
    checkRow,
    onIndustryChange,
    onIndustryCreate,
    onKeywordsInput,
  }
}
