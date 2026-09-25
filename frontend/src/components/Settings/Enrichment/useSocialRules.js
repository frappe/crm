import { toast } from 'frappe-ui'
import { useEnrichmentRules } from './useEnrichmentRules'

// The platforms the Platform dropdown offers. One list, one place to edit it --
// a rule already saved with something else is still shown (see platformOptions).
// TODO: confirm platform list with Pratham
const SOCIAL_PLATFORMS = [
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'Youtube', value: 'youtube' },
  { label: 'X (Twitter)', value: 'twitter' },
]

// The form edits one pattern per rule: the first regex row, which is the shape
// every seeded Social rule has. Anything else on the rule -- a second regex, a
// plain substring added in Desk -- is set aside here so the row can say it isn't
// showing everything, and so the save path can put it back untouched.
function splitPatterns(patternRows) {
  const list = patternRows || []
  const shown = list.find((row) => Number(row.is_regex) === 1)

  return {
    pattern: shown?.pattern || '',
    hidden: list.filter((row) => row !== shown).map((row) => row.pattern),
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

// The dropdown shows a label ("X (Twitter)") while the stored value ("twitter")
// is what actually collides, so a refusal names the platform the way it was
// picked. A platform the list doesn't carry has only its raw value to give.
function platformLabel(platform) {
  const option = SOCIAL_PLATFORMS.find((entry) => entry.value === platform)

  return option?.label || platform
}

export function useSocialRules() {
  const rules = useEnrichmentRules({
    ruleType: 'Social',
    fields: ['target_value'],
    isRowPending,
    buildRow,
    newRow,
    messages: {
      patternsError: __('Could not load rule patterns'),
      refreshError: __('Could not refresh social rules'),
      insertError: __('Could not add social rule'),
      updateError: __('Could not save social rule'),
      deleteError: __('Could not delete social rule'),
      inserted: __('Social rule added successfully'),
      updated: __('Social rule updated successfully'),
      deleted: __('Social rule deleted successfully'),
    },
  })

  function buildRow(rule, patternRows, held) {
    const { pattern, hidden } = splitPatterns(patternRows)

    return {
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      platform: held ? held.platform : rule.target_value || '',
      pattern: held ? held.pattern : pattern,
      // What the server last confirmed. The dirty check and the rollback on a
      // failed save both read from here, never from the inputs.
      savedPlatform: rule.target_value || '',
      savedPattern: pattern,
      hidden,
      error: held ? held.error : '',
    }
  }

  function newRow() {
    return {
      platform: '',
      pattern: '',
      savedPlatform: '',
      savedPattern: '',
      hidden: [],
      error: '',
    }
  }

  // A rule saved with a platform this list doesn't carry still has to appear in
  // its own dropdown -- otherwise the box reads blank and the next save would
  // write that blank over the stored value. The seeded rules alone cover github,
  // facebook and instagram, none of which are in SOCIAL_PLATFORMS yet.
  function platformOptions(row) {
    if (!row.platform) return SOCIAL_PLATFORMS
    if (SOCIAL_PLATFORMS.some((option) => option.value === row.platform)) {
      return SOCIAL_PLATFORMS
    }

    return [...SOCIAL_PLATFORMS, { label: row.platform, value: row.platform }]
  }

  // One platform, one rule. The stored rules are checked on both the value the
  // enricher reads (target_value) and the name the row would take, because a rule
  // renamed or retargeted in Desk can carry one without the other.
  function platformTakenBy(row, platform) {
    const ruleName = socialRuleName(platform)

    return (rules.resource.data || []).find(
      (rule) =>
        rule.name !== row.name &&
        (rule.target_value === platform || rule.rule_name === ruleName),
    )
  }

  // new RegExp is the same engine the box is typed against, so an expression that
  // compiles here is one the admin can reason about. It is not the engine the
  // crawler runs (that is Python's `re`), so this catches typos, not every
  // dialect difference.
  function patternError(pattern) {
    try {
      new RegExp(pattern)
    } catch (err) {
      return __('Not a valid regular expression: {0}', [err.message])
    }

    return ''
  }

  function onPlatformChange(row, value) {
    row.platform = value || ''
    commitRow(row)
  }

  // Keystrokes stay on the row, not in the doc: a half-typed expression is never
  // saved, and the red border clears the moment the admin starts fixing it.
  function onPatternInput(row, value) {
    row.pattern = value
    row.error = ''
  }

  // The one place a row decides whether it has something worth sending. Called by
  // the platform dropdown, by the pattern box on blur/Enter, and by the header
  // Save button.
  function commitRow(row) {
    if (row.saving) return

    // Surrounding space is never part of an expression, and a box holding only
    // space is an empty box. Trimming here rather than on every keystroke lets a
    // space be typed mid-edit; the box visibly snaps to the trimmed value when it
    // is left, which is also what gets compared and sent.
    row.pattern = row.pattern.trim()

    // A pattern that doesn't compile is flagged wherever it was typed, on a
    // stored row or a new one, so leaving the box shows the problem straight
    // away.
    if (row.pattern) {
      row.error = patternError(row.pattern)
      if (row.error) return
    }

    // Only worth asking when the platform is new to this row: re-saving a pattern
    // on an untouched platform must not trip over the row's own rule.
    if (row.platform && (!row.name || row.platform !== row.savedPlatform)) {
      if (platformTakenBy(row, row.platform)) {
        toast.error(
          __('A rule for {0} already exists', [platformLabel(row.platform)]),
        )
        // Back to what is stored -- blank on a row that was never inserted.
        row.platform = row.savedPlatform
        return
      }
    }

    if (!row.name) return insertRow(row)

    if (!row.pattern) {
      row.error = __('Pattern is required')
      return
    }

    if (
      row.platform === row.savedPlatform &&
      row.pattern === row.savedPattern
    ) {
      return
    }

    return updateRow(row)
  }

  // A new row waits on screen until both boxes are filled -- half of one is not a
  // rule, and the doctype would reject it anyway (rule_name and pattern are both
  // required).
  //
  // commitRow has already refused a platform another rule holds; the server's own
  // unique-rule_name error still lands in the insert's catch for anything this
  // list hasn't loaded (a rule added in another tab, an Industry rule).
  function insertRow(row) {
    if (!row.platform || !row.pattern) return

    return rules.insertRow(row, {
      target_value: row.platform,
      match_scope: 'HTML',
      enabled: 1,
      rule_name: socialRuleName(row.platform),
      patterns: [{ pattern: row.pattern, is_regex: 1 }],
    })
  }

  function updateRow(row) {
    const previousPlatform = row.savedPlatform
    const previousPattern = row.savedPattern

    return rules.updateRow(row, {
      mutate: (doc) => {
        doc.target_value = row.platform

        // rule_name carries the platform, so it moves with it -- a rule switched
        // from linkedin to youtube would otherwise still read "Social: linkedin"
        // in Desk. Only rewritten when the platform actually changed, so a rule
        // hand-named in Desk survives an edit to its pattern.
        if (row.platform !== previousPlatform) {
          doc.rule_name = socialRuleName(row.platform)
        }

        const patternRows = doc.patterns || []
        const target = patternRows.find((entry) => Number(entry.is_regex) === 1)
        if (target) target.pattern = row.pattern
        else patternRows.push({ pattern: row.pattern, is_regex: 1 })
        doc.patterns = patternRows
      },
      onSaved: (saved) => {
        const split = splitPatterns(saved.patterns)
        row.hidden = split.hidden
        row.savedPlatform = row.platform
        row.savedPattern = row.pattern
      },
      rollback: () => {
        row.platform = previousPlatform
        row.pattern = previousPattern
        row.error = ''
      },
    })
  }

  // A row the autosave hasn't caught up with: an edit typed but never committed,
  // or a new row whose two halves are both filled and waiting on an insert.
  function isRowPending(row) {
    if (row.saving) return false

    // Compared trimmed, the same way commitRow will send it, so space typed into
    // an otherwise untouched box doesn't light up the Save button.
    const pattern = row.pattern.trim()

    if (!row.name) return Boolean(row.platform && pattern)

    return row.platform !== row.savedPlatform || pattern !== row.savedPattern
  }

  return {
    ...rules,
    commitRow,
    platformOptions,
    onPlatformChange,
    onPatternInput,
  }
}
