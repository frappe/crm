import { toast } from 'frappe-ui'
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

// weight is a Float with a default of 1 and multiplies a rule's hit count in
// extractors.apply_keyword_rules. Zero would silently drop the rule out of the
// score without turning it off, and a negative weight would push against its own
// match -- neither is something a number box should be able to save by accident.
function parseWeight(value) {
  const weight = Number(value)

  if (value === '' || value === null || !Number.isFinite(weight)) return null
  if (weight <= 0) return null

  return weight
}

export function useIndustryRules() {
  const rules = useEnrichmentRules({
    ruleType: 'Industry',
    fields: ['industry', 'weight'],
    isRowPending,
    isRowHeld: (row) =>
      isRowPending(row) || Boolean(row.error) || Boolean(row.weightError),
    buildRow,
    newRow,
    messages: {
      patternsError: __('Could not load rule keywords'),
      refreshError: __('Could not refresh industry rules'),
      insertError: __('Could not add industry rule'),
      updateError: __('Could not save industry rule'),
      deleteError: __('Could not delete industry rule'),
      inserted: __('Industry rule added successfully'),
      updated: __('Industry rule updated successfully'),
      deleted: __('Industry rule deleted successfully'),
    },
  })

  function buildRow(rule, patternRows, held) {
    const { keywords, hidden } = splitPatterns(patternRows)
    // Only a rule that has no weight at all falls back to the doctype's default.
    // A stored 0 is shown as the 0 it is -- the classifier really does score that
    // rule at nothing, and the box claiming 1 would hide it. Editing such a row
    // then fails validation, which is the point at which the admin has to fix it.
    const weight = rule.weight == null ? 1 : Number(rule.weight)

    return {
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      industry: held ? held.industry : rule.industry || '',
      keywords: held ? held.keywords : keywords,
      // The box holds a string, because a half-typed number ("1.") is not one.
      weight: held ? held.weight : String(weight),
      // What the server last confirmed. The dirty check and the rollback on a
      // failed save both read from here, never from the inputs.
      savedIndustry: rule.industry || '',
      savedKeywords: keywords,
      savedWeight: weight,
      hidden,
      error: held ? held.error : '',
      weightError: held ? held.weightError : '',
    }
  }

  function newRow() {
    return {
      industry: '',
      keywords: '',
      // The doctype's default, so a row added and saved untouched scores the same
      // as every seeded rule.
      weight: '1',
      savedIndustry: '',
      savedKeywords: '',
      savedWeight: 1,
      hidden: [],
      error: '',
      weightError: '',
    }
  }

  // One industry, one rule. The stored rules are checked on both the value the
  // classifier reads (industry) and the name the row would take, because a rule
  // renamed or re-pointed in Desk can carry one without the other.
  function industryTakenBy(row, industry) {
    const ruleName = industryRuleName(industry)

    return (rules.resource.data || []).find(
      (rule) =>
        rule.name !== row.name &&
        (rule.industry === industry || rule.rule_name === ruleName),
    )
  }

  function onIndustryChange(row, value) {
    row.industry = value || ''
    commitRow(row)
  }

  // Keystrokes stay on the row, not in the doc: a half-typed list is never saved,
  // and the red border clears the moment the admin starts fixing it.
  function onKeywordsInput(row, value) {
    row.keywords = value
    row.error = ''
  }

  function onWeightInput(row, value) {
    row.weight = value
    row.weightError = ''
  }

  // The one place a row decides whether it has something worth sending. Called by
  // the industry picker, by the keywords and weight boxes on blur/Enter, and by
  // the header Save button.
  function commitRow(row) {
    if (row.saving) return

    const keywords = parseKeywords(row.keywords)
    // The box snaps to what will actually be stored when it is left, so the
    // admin sees the trimming and de-duplication rather than guessing at it.
    row.keywords = keywords.join(', ')

    const weight = parseWeight(row.weight)
    if (weight === null) {
      row.weightError = __('Weight must be greater than 0')
      return
    }
    // Same as the keywords box above: what is on screen becomes exactly what a
    // save would store, so "1.0" settles to "1" instead of reading as an edit
    // forever after.
    row.weight = String(weight)

    // A rule with no industry classifies nothing, and the Link's Clear button can
    // empty a stored one. Put it back rather than save a rule that does nothing.
    if (!row.industry && row.name) {
      toast.error(__('Industry is required'))
      row.industry = row.savedIndustry
      return
    }

    // Only worth asking when the industry is new to this row: re-saving keywords
    // on an untouched industry must not trip over the row's own rule.
    if (row.industry && (!row.name || row.industry !== row.savedIndustry)) {
      if (industryTakenBy(row, row.industry)) {
        toast.error(__('A rule for {0} already exists', [row.industry]))
        // Back to what is stored -- blank on a row that was never inserted.
        row.industry = row.savedIndustry
        return
      }
    }

    if (!row.name) return insertRow(row, keywords, weight)

    if (!keywords.length) {
      row.error = __('At least one keyword is required')
      return
    }

    if (
      row.industry === row.savedIndustry &&
      row.keywords === row.savedKeywords &&
      weight === row.savedWeight
    ) {
      return
    }

    return updateRow(row, keywords, weight)
  }

  // A new row waits on screen until it has an industry and at least one keyword
  // -- half of one is not a rule, and the doctype would reject it anyway
  // (rule_name is required, and a rule with no patterns never matches). Rule and
  // keywords go in as one document, so a failed insert leaves nothing
  // half-created behind.
  //
  // commitRow has already refused an industry another rule holds; the server's
  // own unique-rule_name error still lands in the insert's catch for anything
  // this list hasn't loaded (a rule added in another tab, a Social rule).
  function insertRow(row, keywords, weight) {
    if (!row.industry || !keywords.length) return

    return rules.insertRow(row, {
      industry: row.industry,
      weight,
      // What the seeded Industry rules score against: the company name,
      // description, title and headings, never body copy (see
      // extractors.classify_industry).
      match_scope: 'Headline',
      enabled: 1,
      rule_name: industryRuleName(row.industry),
      patterns: keywords.map((keyword) => ({ pattern: keyword, is_regex: 0 })),
    })
  }

  function updateRow(row, keywords, weight) {
    const previousIndustry = row.savedIndustry
    const previousKeywords = row.savedKeywords
    const previousWeight = row.savedWeight

    return rules.updateRow(row, {
      mutate: (doc) => {
        doc.industry = row.industry
        doc.weight = weight

        // rule_name carries the industry, so it moves with it -- a rule switched
        // from Finance to Manufacturing would otherwise still read the old name
        // in Desk. Only rewritten when the industry actually changed, so a rule
        // hand-named in Desk survives an edit to its keywords.
        if (row.industry !== previousIndustry) {
          doc.rule_name = industryRuleName(row.industry)
        }

        const patternRows = doc.patterns || []
        // A keyword that is still in the box keeps its existing child row, so an
        // untouched keyword isn't dropped and re-created on every save.
        const existing = new Map(
          patternRows
            .filter(isKeywordRow)
            .map((entry) => [entry.pattern, entry]),
        )

        doc.patterns = [
          ...keywords.map(
            (keyword) =>
              existing.get(keyword) || { pattern: keyword, is_regex: 0 },
          ),
          // The rows the box never owned, carried across as the very objects that
          // were read, and last so the box's own rows keep the order they were
          // typed in.
          ...patternRows.filter((entry) => !isKeywordRow(entry)),
        ]
      },
      onSaved: (saved) => {
        // Read back from the server rather than from the box, so what is on
        // screen is exactly what was stored.
        const split = splitPatterns(saved.patterns)
        row.keywords = split.keywords
        row.savedKeywords = split.keywords
        row.hidden = split.hidden
        row.savedIndustry = row.industry
        row.savedWeight = weight
        row.weight = String(weight)
      },
      rollback: () => {
        row.industry = previousIndustry
        row.keywords = previousKeywords
        row.weight = String(previousWeight)
        row.error = ''
        row.weightError = ''
      },
    })
  }

  // A row the autosave hasn't caught up with: an edit typed but never committed,
  // or a new row with both an industry and a keyword, waiting on an insert.
  function isRowPending(row) {
    if (row.saving) return false

    // Compared the way commitRow will send it, so space or a trailing comma typed
    // into an otherwise untouched box doesn't light up the Save button.
    const keywords = parseKeywords(row.keywords).join(', ')

    if (!row.name) return Boolean(row.industry && keywords)

    // The weight is compared as text, because a stored value the box would refuse
    // (a 0 written in Desk) still has to read as untouched until it is edited.
    // Once it is edited the row is pending, Save flushes it, and commitRow is
    // what puts the error under the box.
    return (
      row.industry !== row.savedIndustry ||
      keywords !== row.savedKeywords ||
      String(row.weight).trim() !== String(row.savedWeight)
    )
  }

  return {
    ...rules,
    commitRow,
    onIndustryChange,
    onKeywordsInput,
    onWeightInput,
  }
}
