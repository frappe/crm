import { call } from 'frappe-ui'
import { useEnrichmentRules } from './useEnrichmentRules'

// Which pattern rows the comma-separated box is allowed to own -- the rest are
// held aside, shown only as a count, and written back exactly as they were read.
//
// is_regex=1 rows are excluded because config._compile_pattern escapes a keyword
// but compiles a regex verbatim, so a regex written in Desk would be mangled the
// moment it made a round trip through the box. A plain keyword that contains a
// comma is excluded for the same reason: the box would split it in two on the
// next save.
function isKeywordRow(row) {
  return Number(row.is_regex) !== 1 && !String(row.pattern).includes(',')
}

// An Industry rule's keywords are one child row each, but a list of plain words
// reads far better as one comma-separated box than as a stack of inputs -- so the
// box is the list, joined for display and split again on the way back. It is put
// through parseKeywords on the way out too, so what is on screen is exactly what
// a save would store and an untouched rule never reads as edited.
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

// The box back into child rows: split on commas, trim, drop the empties a
// trailing comma or a double comma leaves behind, and drop repeats. Matching is
// case-insensitive downstream (config._compile_pattern compiles with re.I), so
// "OEM" and "oem" are the same keyword; the first spelling typed is the one kept.
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

// Deliberately the same shape install.py seeds ("Industry: Manufacturing", see
// _seed_industry_rules), so an industry that is already seeded collides on the
// unique rule_name instead of quietly getting a second rule.
//
// Not run through __(): rule_name is stored data that has to match a string
// Python wrote, so a translated UI must not change it.
function industryRuleName(industry) {
  return `Industry: ${industry}`
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
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      industry: held ? held.industry : rule.industry || '',
      keywords: held ? held.keywords : keywords,
      // Set when the admin picked "Create New" for an industry that doesn't
      // exist yet; Save inserts the CRM Industry before the rule that links it.
      newIndustry: held ? held.newIndustry : false,
      // What the server last confirmed. The dirty check reads from here, never
      // from the inputs.
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

  // Compared the way Save will send it, so space or a trailing comma typed into
  // an otherwise untouched box doesn't light up the badge.
  function isRowChanged(row) {
    return (
      row.industry !== row.savedIndustry ||
      parseKeywords(row.keywords).join(', ') !== row.savedKeywords
    )
  }

  // One industry, one rule, checked on both the value the classifier reads
  // (industry) and the name the row would take, the same way the Social rows
  // are. CRM Industry names are compared case-insensitively because the
  // database's unique index on them is.
  function industryTakenBy(industry, others) {
    const folded = industry.toLowerCase()
    const ruleName = industryRuleName(industry).toLowerCase()

    return others.find((other) => {
      const otherIndustry = (other.industry || '').toLowerCase()
      if (otherIndustry === folded) return true

      return (
        Boolean(other.ruleName) &&
        other.industry === other.savedIndustry &&
        other.ruleName.toLowerCase() === ruleName
      )
    })
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

  // Also run when the keywords box is left or an industry is picked, so a
  // problem is flagged straight away instead of on Save. The box snaps to what
  // will actually be stored, so the admin sees the trimming and de-duplication
  // rather than guessing at it.
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

  // The Link's "Create New": the typed text becomes the row's industry now, and
  // the CRM Industry itself is only inserted on Save, so abandoning the row
  // leaves no stray industry behind.
  function onIndustryCreate(row, value, close) {
    const industry = (value || '').trim()
    // Nothing typed: leave the menu open so the admin can type one.
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

  // CRM Industry is named by its industry field, so a DuplicateEntryError means
  // it already exists -- created by another row in this same Save, or by
  // someone else meanwhile -- which is all the rule needs.
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
      rule_name: industryRuleName(row.industry),
      industry: row.industry,
      // The doctype's default and what every seeded rule has. weight multiplies
      // the rule's hits in extractors.py, so it is set explicitly rather than
      // left to a default that might not apply to an API insert.
      weight: 1,
      // What the seeded Industry rules score against: the company name,
      // description, title and headings, never body copy.
      match_scope: 'Headline',
      patterns: parseKeywords(row.keywords).map((keyword) => ({
        pattern: keyword,
        is_regex: 0,
      })),
    }
  }

  // Only what the row owns is sent: industry, patterns and, when the industry
  // changed, rule_name. weight is never sent, so an existing rule keeps the
  // weight it already has. `doc` is the rule as stored right now.
  async function toUpdate(row, doc) {
    await ensureIndustry(row)

    const values = { industry: row.industry }

    // rule_name carries the industry, so it moves with it. Only rewritten when
    // the industry actually changed, so a rule hand-named in Desk survives an
    // edit to its keywords.
    if (row.industry !== row.savedIndustry) {
      values.rule_name = industryRuleName(row.industry)
    }

    const patternRows = doc.patterns || []
    // A keyword that is still in the box keeps its existing child row, so an
    // untouched keyword isn't dropped and re-created on every save.
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
      // The rows the box never owned, carried across as they were read, and
      // last so the box's own rows keep the order they were typed in.
      ...patternRows.filter((entry) => !isKeywordRow(entry)).map(pick),
    ]

    return values
  }

  // A row just added with nothing picked or typed into it yet.
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
