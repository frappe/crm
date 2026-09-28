import { useEnrichmentRules } from './useEnrichmentRules'

// The networks mapper.py can write to a CRM field (_SOCIAL_KEYS there). A rule
// for any other network would match on the page and then never populate
// anything, so the Platform box only offers these.
export const SOCIAL_PLATFORMS = [
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'X (Twitter)', value: 'twitter' },
  { label: 'GitHub', value: 'github' },
  { label: 'Facebook', value: 'facebook' },
  { label: 'Instagram', value: 'instagram' },
  { label: 'YouTube', value: 'youtube' },
]

// mapper.py looks a social profile up by its exact lowercase key, so a value
// stored in Desk as "LinkedIn " still reads as the same platform.
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
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      platform: held ? held.platform : rule.target_value || '',
      pattern: held ? held.pattern : pattern,
      // What the server last confirmed. The dirty check reads from here, never
      // from the inputs.
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
    } else if (!SOCIAL_PLATFORMS.some((option) => option.value === platform)) {
      row.platformError = __('Enrichment cannot fill a field from {0}', [
        platform,
      ])
    } else if (platformTakenBy(platform, others)) {
      row.platformError = __('A rule for {0} already exists', [platform])
    }

    // Whether the regex compiles is left to the server: the crawler runs
    // Python's `re`, so that is the engine CRM Enrichment Rule validates
    // against, and its message comes back under the row.
    if (!pattern) {
      row.patternError = __('Pattern is required')
    }

    return !row.platformError && !row.patternError
  }

  // Also run when a box is left, so a taken platform is flagged
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

  // A row just added with nothing typed into it yet.
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
