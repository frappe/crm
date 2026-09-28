import { useEnrichmentRules } from './useEnrichmentRules'

// mapper.py looks a social profile up by its exact lowercase key, so whatever
// the admin types is stored trimmed and lowercased -- "LinkedIn " and
// "linkedin" are the same platform.
function normalizePlatform(value) {
  return (value || '').trim().toLowerCase()
}

// The row edits the rule's first pattern, which is the only one every seeded
// Social rule has. Anything after it -- a second regex, a plain substring added
// in Desk -- is set aside so the row can say it isn't showing everything, and so
// the save path can put it back untouched.
function splitPatterns(patternRows) {
  const [first, ...rest] = patternRows || []

  return {
    pattern: first?.pattern || '',
    // A first pattern written in Desk as a plain substring is still one; only a
    // regex row (or a new one) is held to the regex check.
    patternIsRegex: first ? Number(first.is_regex) === 1 : true,
    hidden: rest.map((row) => row.pattern),
  }
}

// Deliberately the same shape install.py seeds ("Social: linkedin", see
// _seed_social_rules), so a platform that is already seeded collides on the
// unique rule_name instead of quietly getting a second rule.
//
// Not run through __(): rule_name is stored data that has to match a string
// Python wrote, so a translated UI must not change it.
function socialRuleName(platform) {
  return `Social: ${platform}`
}

// new RegExp is the same engine the box is typed against, so an expression that
// compiles here is one the admin can reason about. It is not the engine the
// crawler runs (that is Python's `re`), so this catches typos, not every
// dialect difference.
function regexError(pattern) {
  try {
    new RegExp(pattern)
  } catch (err) {
    return __('Not a valid regular expression: {0}', [err.message])
  }

  return ''
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
    const { pattern, patternIsRegex, hidden } = splitPatterns(patternRows)

    return {
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      platform: held ? held.platform : rule.target_value || '',
      pattern: held ? held.pattern : pattern,
      // What the server last confirmed. The dirty check reads from here, never
      // from the inputs.
      savedPlatform: rule.target_value || '',
      savedPattern: pattern,
      patternIsRegex,
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
      patternIsRegex: true,
      hidden: [],
      platformError: '',
      patternError: '',
    }
  }

  function clearErrors(row) {
    row.platformError = ''
    row.patternError = ''
  }

  // Compared trimmed, the way Save will send it, so space typed into an
  // otherwise untouched box doesn't light up the badge. The platform is compared
  // as typed rather than normalized: a rule stored as "LinkedIn" in Desk isn't
  // an edit until the admin touches it.
  function isRowChanged(row) {
    return (
      row.platform.trim() !== row.savedPlatform ||
      row.pattern.trim() !== row.savedPattern
    )
  }

  // One platform, one rule. Every other row on screen is checked on both the
  // value the enricher reads (target_value) and the name the row would take,
  // because a rule renamed in Desk can carry one without the other. A row whose
  // platform is changing in this same Save gives up its rule_name with it, so
  // only a row keeping its platform still holds the name.
  function platformTakenBy(platform, others) {
    const ruleName = socialRuleName(platform).toLowerCase()

    return others.find((other) => {
      const otherPlatform = normalizePlatform(other.platform)
      if (otherPlatform === platform) return true

      return (
        Boolean(other.ruleName) &&
        otherPlatform === normalizePlatform(other.savedPlatform) &&
        other.ruleName.toLowerCase() === ruleName
      )
    })
  }

  function validateRow(row, others) {
    const platform = normalizePlatform(row.platform)
    const pattern = row.pattern.trim()

    if (!platform) {
      row.platformError = __('Platform is required')
    } else if (platformTakenBy(platform, others)) {
      row.platformError = __('A rule for {0} already exists', [platform])
    }

    if (!pattern) {
      row.patternError = __('Pattern is required')
    } else if (row.patternIsRegex) {
      row.patternError = regexError(pattern)
    }

    return !row.platformError && !row.patternError
  }

  // Also run when a box is left, so a bad regex or a taken platform is flagged
  // straight away instead of on Save. Only a changed row is checked: a stored
  // rule nobody touched is not the admin's problem to fix here.
  function checkRow(row) {
    row.pattern = row.pattern.trim()
    if (!row.name || isRowChanged(row)) {
      clearErrors(row)
      validateRow(
        row,
        rules.rows.value.filter((other) => other !== row),
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
    const platform = normalizePlatform(row.platform)

    return {
      rule_name: socialRuleName(platform),
      target_value: platform,
      match_scope: 'HTML',
      enabled: 1,
      patterns: [{ pattern: row.pattern.trim(), is_regex: 1 }],
    }
  }

  // Only what the row owns is sent: target_value, patterns and, when the
  // platform changed, rule_name. `doc` is the rule as stored right now.
  function toUpdate(row, doc) {
    const platform = normalizePlatform(row.platform)
    const values = { target_value: platform }

    // rule_name carries the platform, so it moves with it -- a rule switched
    // from linkedin to youtube would otherwise still read "Social: linkedin" in
    // Desk. A case-only change ("LinkedIn" -> "linkedin") is the same platform,
    // so a rule hand-named in Desk keeps its name through a pattern edit.
    if (platform !== normalizePlatform(row.savedPlatform)) {
      values.rule_name = socialRuleName(platform)
    }

    // The first pattern takes the box; every other row goes back exactly as it
    // was read, name included, so set_value updates them in place instead of
    // dropping and re-creating them.
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

  return {
    ...rules,
    checkRow,
    onPlatformInput,
    onPatternInput,
  }
}
