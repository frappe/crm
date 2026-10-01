import { useEnrichmentRules } from './useEnrichmentRules'

// Not a whitelist; only these map to CRM fields (_SOCIAL_KEYS in mapper.py).
// Patterns mirror SOCIAL_PATTERNS in crm/domain_enrichment/install.py; keep
// them in sync.
export const SOCIAL_PLATFORMS = [
  {
    label: 'LinkedIn',
    value: 'linkedin',
    pattern: 'linkedin\\.com/(company|in|school)/',
  },
  {
    label: 'X (Twitter)',
    value: 'twitter',
    pattern: '(twitter\\.com|x\\.com)/[A-Za-z0-9_]+',
  },
  {
    label: 'GitHub',
    value: 'github',
    pattern: 'github\\.com/[A-Za-z0-9_.-]+',
  },
  {
    label: 'Facebook',
    value: 'facebook',
    pattern: 'facebook\\.com/[A-Za-z0-9_.\\-/]+',
  },
  {
    label: 'Instagram',
    value: 'instagram',
    pattern: 'instagram\\.com/[A-Za-z0-9_.]+',
  },
  {
    label: 'YouTube',
    value: 'youtube',
    pattern: 'youtube\\.com/(channel/|c/|user/|@)[A-Za-z0-9_.\\-]+',
  },
]

// mapper.py keys profiles by exact lowercase name, so "LinkedIn " from Desk is
// the same platform.
export function normalizePlatform(value) {
  return (value || '').trim().toLowerCase()
}

export function isKnownPlatform(platform) {
  const value = normalizePlatform(platform)
  return SOCIAL_PLATFORMS.some((option) => option.value === value)
}

function defaultPattern(platform) {
  const value = normalizePlatform(platform)
  return SOCIAL_PLATFORMS.find((option) => option.value === value)?.pattern
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

// Same shape install.py seeds, so re-adding a seeded platform collides on the
// unique rule_name.
// Not run through __(): rule_name is stored data matching what Python wrote.
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

  // Trimmed like Save sends it; platform isn't normalized so Desk's "LinkedIn"
  // isn't an edit until touched.
  function isRowChanged(row) {
    return (
      row.platform.trim() !== row.savedPlatform ||
      row.pattern.trim() !== row.savedPattern
    )
  }

  // Check target_value and rule_name: a rule renamed in Desk can match on one
  // but not the other.
  // A row changing platform in this Save releases its rule_name, so it no
  // longer holds it.
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

  // Swap in the new default only while the pattern is still the old one, so
  // custom regexes survive.
  function onPlatformInput(row, value) {
    const pattern = row.pattern.trim()
    if (!pattern || pattern === defaultPattern(row.platform)) {
      row.pattern = defaultPattern(value) || ''
      row.patternError = ''
    }

    row.platform = value
    row.platformError = ''
    row.serverError = ''
  }

  function onPlatformCreate(row, value, close) {
    const platform = normalizePlatform(value)
    if (!platform) return

    onPlatformInput(row, platform)
    checkRow(row)
    // The pattern is still checked on Save.
    if (!row.pattern) row.patternError = ''
    close()
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

  function toUpdate(row, doc) {
    const platform = normalizePlatform(row.platform)
    const values = { target_value: platform }

    // Renamed with the platform, but not on a case-only change, so Desk
    // hand-named rules survive.
    if (platform !== normalizePlatform(row.savedPlatform)) {
      values.rule_name = socialRuleName(platform)
    }

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
    onPlatformCreate,
    onPatternInput,
  }
}
