import { useEnrichmentRules } from './useEnrichmentRules'

// The server lowercases platforms on save; this matches its case-insensitive
// duplicate check.
function normalizePlatform(value) {
  return (value || '').trim().toLowerCase()
}

// Only the first pattern is editable (every seeded rule has one); the rest are
// kept aside untouched.
function splitPatterns(patternRows) {
  const [first, ...rest] = patternRows || []

  return {
    pattern: first?.pattern || '',
    hidden: rest.map((row) => row.pattern),
  }
}

export function useSocialRules() {
  const rules = useEnrichmentRules({
    ruleType: 'Social',
    fields: ['target_value'],
    buildRow,
    newRow,
    isRowChanged,
    validateRow,
    toInsert,
    toUpdate,
    clearErrors,
    messages: {
      insertError: __('Could not add social rule'),
      updateError: __('Could not save social rule'),
      deleteError: __('Could not delete social rule'),
    },
  })

  function buildRow(rule, patternRows, held) {
    const { pattern, hidden } = splitPatterns(patternRows)

    return {
      platform: held ? held.platform : rule.target_value || '',
      pattern: held ? held.pattern : pattern,
      savedPlatform: rule.target_value || '',
      savedPattern: pattern,
      hidden,
      platformError: held ? held.platformError : '',
      patternError: held ? held.patternError : '',
    }
  }

  function newRow() {
    return {
      platform: '',
      pattern: '',
      savedPlatform: '',
      savedPattern: '',
      hidden: [],
      platformError: '',
      patternError: '',
    }
  }

  function clearErrors(row) {
    row.platformError = ''
    row.patternError = ''
  }

  // Trimmed like Save sends it.
  function isRowChanged(row) {
    return (
      row.platform.trim() !== row.savedPlatform ||
      row.pattern.trim() !== row.savedPattern
    )
  }

  // Case-insensitive like the server's duplicate check.
  function platformTakenBy(platform, others) {
    return others.some(
      (other) => normalizePlatform(other.platform) === platform,
    )
  }

  function validateRow(row, others) {
    const platform = normalizePlatform(row.platform)
    const pattern = row.pattern.trim()

    if (!platform) {
      row.platformError = __('Platform is required')
    } else if (platformTakenBy(platform, others)) {
      row.platformError = __('A rule for {0} already exists', [platform])
    }

    // Regex validity is left to the server, which compiles with Python's `re`
    // like the crawler.
    if (!pattern) {
      row.patternError = __('Pattern is required')
    }

    return !row.platformError && !row.patternError
  }

  // Untouched stored rows aren't checked: their problems aren't the admin's to
  // fix here.
  function checkRow(row) {
    row.pattern = row.pattern.trim()
    if (!row.name || isRowChanged(row)) {
      clearErrors(row)
      validateRow(
        row,
        rules.rows.value.filter((other) => other !== row && !other.removed),
      )
    }
  }

  function onPlatformInput(row, value) {
    row.platform = value
    row.platformError = ''
    row.serverError = ''
  }

  function onPatternInput(row, value) {
    row.pattern = value
    row.patternError = ''
    row.serverError = ''
  }

  function toInsert(row) {
    return {
      target_value: row.platform.trim(),
      match_scope: 'HTML',
      patterns: [{ pattern: row.pattern.trim(), is_regex: 1 }],
    }
  }

  function toUpdate(row, doc) {
    const values = { target_value: row.platform.trim() }

    // Child row names are kept so set_value updates them in place instead of
    // re-creating them.
    const [first, ...rest] = doc.patterns || []
    values.patterns = [
      first
        ? {
            name: first.name,
            pattern: row.pattern.trim(),
            is_regex: first.is_regex,
          }
        : { pattern: row.pattern.trim(), is_regex: 1 },
      ...rest.map(({ name, pattern, is_regex }) => ({
        name,
        pattern,
        is_regex,
      })),
    ]

    return values
  }

  function isRowBlank(row) {
    return !row.name && !row.platform.trim() && !row.pattern.trim()
  }

  return {
    ...rules,
    isRowBlank,
    checkRow,
    onPlatformInput,
    onPatternInput,
  }
}
