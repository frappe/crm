<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5 items-center">
          {{ __('Enrichment') }}
          <Badge
            v-if="hasUnsavedChanges && !settings.save.loading"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
            size="sm"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Set up enrichment availability and match website data to CRM fields.',
            )
          }}
        </p>
      </div>
      <div class="flex items-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Save')"
          variant="solid"
          :loading="settings.save.loading"
          :disabled="!hasUnsavedChanges"
          @click="save"
        />
      </div>
    </div>

    <div
      v-if="settings.get.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-8" />
    </div>
    <Tabs
      v-else
      v-model="tabIndex"
      as="div"
      :tabs="tabOptions"
      class="[&_[role='tablist']]:px-2 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel="{ tab }">
        <div
          v-if="tab.value === 'general'"
          class="flex-1 flex flex-col overflow-y-auto"
        >
          <div class="flex gap-4 items-center justify-between py-3 px-2">
            <div class="flex flex-col">
              <div class="text-p-base-medium text-ink-gray-7 truncate">
                {{ __('Enrich') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Master switch for the Domain Enrichment feature.') }}
              </div>
            </div>
            <div>
              <Switch
                :model-value="Boolean(settings.doc.enabled)"
                size="sm"
                @update:model-value="(value) => update('enabled', value)"
              />
            </div>
          </div>

          <div class="h-px border-t mx-2 border-outline-elevation-2" />

          <div
            class="flex items-center justify-between text-lg-semibold mt-4 py-3 px-2"
            :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-8'"
          >
            {{ __('Crawl settings') }}
          </div>
          <div class="flex gap-4 items-center justify-between py-3 px-2">
            <div class="flex flex-col">
              <div
                class="text-p-base-medium truncate"
                :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-7'"
              >
                {{ __('Max pages') }}
              </div>
              <div
                class="text-p-sm"
                :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-5'"
              >
                {{
                  __(
                    'Maximum number of pages that can be crawled during a single enrichment run.',
                  )
                }}
              </div>
            </div>
            <div>
              <FormControl
                :model-value="pending.max_pages ?? settings.doc.max_pages"
                type="number"
                min="1"
                class="w-24"
                :disabled="enrichmentOff"
                @update:model-value="(value) => (pending.max_pages = value)"
                @blur="save"
                @keyup.enter="save"
              />
            </div>
          </div>

          <div class="h-px border-t mx-2 border-outline-elevation-2" />

          <div
            class="flex items-center justify-between text-lg-semibold mt-4 py-3 px-2"
            :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-8'"
          >
            {{ __('Automation') }}
          </div>
          <div class="flex gap-4 items-center justify-between py-3 px-2">
            <div class="flex flex-col">
              <div
                class="text-p-base-medium truncate"
                :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-7'"
              >
                {{ __('Auto-enrich new Organizations') }}
              </div>
              <div
                class="text-p-sm"
                :class="enrichmentOff ? 'text-ink-gray-4' : 'text-ink-gray-5'"
              >
                {{
                  __(
                    'Automatically enrich a CRM Organization in the background as soon as it is created (requires a website). When off, enrichment is triggered manually via the Enrich button.',
                  )
                }}
              </div>
            </div>
            <div>
              <Switch
                :model-value="Boolean(settings.doc.auto_enrich)"
                size="sm"
                :disabled="enrichmentOff"
                @update:model-value="(value) => update('auto_enrich', value)"
              />
            </div>
          </div>
        </div>

        <div v-else class="flex-1 flex flex-col overflow-y-auto">
          <div class="flex items-start justify-between gap-4 py-3 px-2">
            <div class="flex flex-col gap-1">
              <div class="text-lg-semibold text-ink-gray-8">
                {{ __('Social profile rules') }}
              </div>
              <!-- Placeholder copy lifted from the design; the real subtitle
                   replaces it once the wording is settled. -->
              <div class="text-p-sm text-ink-gray-6 max-w-lg">
                {{
                  __('Allow users to enrich leads when a website is available.')
                }}
              </div>
            </div>
            <Button
              :label="__('Add Social')"
              variant="subtle"
              icon-left="lucide-plus"
              @click="addSocialRule"
            />
          </div>

          <div
            v-if="rulesLoading"
            class="flex flex-1 items-center justify-center"
          >
            <LoadingIndicator class="size-4" />
          </div>
          <!-- Only stands in for the rows when there are none: a reload that
               fails after the first load keeps the rows up and toasts instead. -->
          <div
            v-else-if="socialRules.list.error && !rows.length"
            class="flex flex-1 flex-col items-center justify-center gap-3"
          >
            <div class="text-p-base text-ink-gray-6 text-center">
              {{
                socialRules.list.error.messages?.[0] ||
                __('Could not load social rules')
              }}
            </div>
            <Button :label="__('Retry')" @click="retry" />
          </div>
          <EmptyState
            v-else-if="!rows.length"
            class="flex-1"
            name="Social Rules"
            :title="__('No social rules found')"
            :description="
              __('Add one to tell enrichment which profile links to look for.')
            "
            icon="share-2"
          />
          <div v-else class="flex flex-col gap-3 py-2 px-2">
            <div
              v-for="row in rows"
              :key="row.key"
              class="flex items-start gap-2"
            >
              <Select
                :model-value="row.platform || undefined"
                :options="platformOptions(row)"
                :placeholder="__('Platform')"
                class="w-40 shrink-0"
                :class="row.enabled ? '' : 'opacity-60'"
                @update:model-value="(value) => onPlatformChange(row, value)"
              />
              <div
                class="flex-1 min-w-0"
                :class="row.enabled ? '' : 'opacity-60'"
              >
                <FormControl
                  :model-value="row.pattern"
                  type="text"
                  :placeholder="__('Regex pattern')"
                  class="[&_input]:font-mono"
                  :class="
                    row.error
                      ? '[&_input]:!border-outline-red-2 [&_input]:focus:!border-outline-red-2'
                      : ''
                  "
                  @update:model-value="(value) => onPatternInput(row, value)"
                  @blur="commitRow(row)"
                  @keyup.enter="commitRow(row)"
                />
                <ErrorMessage
                  v-if="row.error"
                  class="mt-1"
                  :message="row.error"
                />
                <Tooltip
                  v-else-if="row.hidden.length"
                  :text="row.hidden.join('  |  ')"
                >
                  <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                    {{
                      __('+{0} more pattern(s) on this rule', [
                        row.hidden.length,
                      ])
                    }}
                  </div>
                </Tooltip>
              </div>
              <!-- Shown only when the rule is off, the way HierarchyRow.vue
                   marks a disabled user. Outside the dimmed columns so it stays
                   readable, and outside the menu because turning a rule back on
                   isn't wired up yet. -->
              <Badge
                v-if="!row.enabled"
                :label="__('Disabled')"
                theme="gray"
                variant="subtle"
                size="sm"
                class="mt-1 shrink-0"
              />
              <Dropdown placement="right" :options="rowOptions(row)">
                <Button
                  icon="lucide-more-horizontal"
                  variant="ghost"
                  @click="isConfirmingDelete = false"
                />
              </Dropdown>
            </div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  call,
  createDocumentResource,
  createListResource,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Select,
  Switch,
  Tabs,
  toast,
  Tooltip,
} from 'frappe-ui'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { ConfirmDelete } from '@/utils'
import { computed, reactive, ref, watch } from 'vue'

// The platforms the Platform dropdown offers. One list, one place to edit it --
// a rule already saved with something else is still shown (see platformOptions).
// TODO: confirm platform list with Pratham
const SOCIAL_PLATFORMS = [
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'Youtube', value: 'youtube' },
  { label: 'X (Twitter)', value: 'twitter' },
]

const settings = createDocumentResource({
  doctype: 'CRM Enrichment Settings',
  name: 'CRM Enrichment Settings',
  auto: true,
})

// frappe-ui's Tabs is index-based; `value` rides along on each tab so the panels
// key off a stable id rather than a translated label.
const tabIndex = ref(0)

const tabOptions = [
  { label: __('General'), value: 'general' },
  { label: __('Rules'), value: 'rules' },
]

// Only Social rules for now -- Industry rules score a classification and read
// nothing like a platform/pattern pair, so they get their own list later.
// order_by matches the doctype's own sort (modified desc), so the list reads the
// same here as it does in Desk.
const socialRules = createListResource({
  doctype: 'CRM Enrichment Rule',
  filters: { rule_type: 'Social' },
  fields: ['name', 'rule_name', 'target_value', 'enabled'],
  orderBy: 'modified desc',
  pageLength: 99,
  auto: true,
  onSuccess: (rules) => loadPatterns(rules),
})

// rule name -> the rule's pattern child rows, as stored
const patterns = reactive({})
const patternsLoading = ref(false)

// The spinner stands in for the whole section, so it only belongs on the first
// load. A reload after an insert or a delete leaves the rows on screen and swaps
// them when the new ones land.
const loadedOnce = ref(false)

// createListResource keeps its fetch state on `.list`, not on the resource
// itself -- the patterns land after it, so the spinner has to cover both.
const rulesLoading = computed(
  () =>
    !loadedOnce.value && (socialRules.list.loading || patternsLoading.value),
)

// reload() rethrows on a second failure, and an unguarded rejection here would
// only show up as console noise -- the error state already renders the message.
function retry() {
  socialRules.reload().catch(() => {})
}

// A reload after an insert or a delete no longer blanks the section, so a failure
// would otherwise leave the old rows up with nothing said. The rows are still
// the last thing the server confirmed, so they stay -- the toast is what tells
// the admin the list may have drifted.
function reloadRules() {
  socialRules.reload().catch(() => {
    toast.error(__('Could not refresh social rules'))
  })
}

// get_list never returns child tables, so the patterns have to be fetched
// separately: one frappe.client.get per rule, which is what the rest of Settings
// already does for a single doc (see WorkflowAutomationDetail.vue). A handful of
// Social rules means a handful of parallel requests -- cheaper than adding a
// backend endpoint for a read-only list. createDocumentResource per rule was the
// other option, but a resource can't be created inside v-for: it would have to
// be built and cached outside the render, and its save/setValue machinery is
// dead weight next to the plain get/save this form already makes.
async function loadPatterns(rules) {
  if (!rules?.length) {
    savedRows.value = []
    loadedOnce.value = true
    return
  }

  patternsLoading.value = true
  try {
    const docs = await Promise.all(
      rules.map((rule) =>
        call('frappe.client.get', {
          doctype: 'CRM Enrichment Rule',
          name: rule.name,
        }),
      ),
    )
    docs.forEach((doc) => {
      patterns[doc.name] = doc.patterns || []
    })
    buildRows(rules)
  } catch (err) {
    // A row with no patterns loaded would read as an empty pattern box, and
    // saving that box would wipe the stored pattern -- so drop the rows rather
    // than offer edits built on a half-loaded rule.
    savedRows.value = []
    toast.error(err.messages?.[0] || __('Could not load rule patterns'))
  } finally {
    patternsLoading.value = false
    loadedOnce.value = true
  }
}

// ---------------------------------------------------------------------------
// Social rule rows
// ---------------------------------------------------------------------------

// One editable row per stored rule, rebuilt whenever the list reloads.
const savedRows = ref([])

// Rows added by "+ Add Social" that have nothing behind them yet. They live
// apart from savedRows so a reload rebuilds the stored rows without sweeping
// away a half-filled new one.
const localRows = ref([])

let localRowSeq = 0

const rows = computed(() => [...savedRows.value, ...localRows.value])

// The dropdown menu's Delete asks first by swapping itself for "Confirm Delete",
// which is how every other Settings list confirms (see SlaPriorityList.vue). One
// flag for the page: only one menu is ever open.
const isConfirmingDelete = ref(false)

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

function buildRows(rules) {
  // Every row is rebuilt from the reload, so whatever the admin still had in
  // flight on a row that survived is carried across: the values in its boxes and
  // the error under them. Otherwise deleting one row would quietly discard a
  // half-typed expression, or a red border, on another.
  const carried = new Map()
  savedRows.value.forEach((row) => {
    if (isRowPending(row) || row.error) carried.set(row.name, row)
  })

  savedRows.value = rules.map((rule) => {
    const { pattern, hidden } = splitPatterns(patterns[rule.name])
    const held = carried.get(rule.name)

    return reactive({
      key: rule.name,
      name: rule.name,
      // The stored values below always come from the reload; only what was being
      // edited is laid back on top of them.
      platform: held ? held.platform : rule.target_value || '',
      pattern: held ? held.pattern : pattern,
      // What the server last confirmed. The dirty check and the rollback on a
      // failed save both read from here, never from the inputs.
      savedPlatform: rule.target_value || '',
      savedPattern: pattern,
      enabled: Boolean(rule.enabled),
      hidden,
      error: held ? held.error : '',
      saving: false,
    })
  })
}

function addSocialRule() {
  localRows.value.push(
    reactive({
      key: `new-${(localRowSeq += 1)}`,
      name: null,
      platform: '',
      pattern: '',
      savedPlatform: '',
      savedPattern: '',
      // Inserted as enabled, so the row shouldn't read as disabled while local.
      enabled: true,
      hidden: [],
      error: '',
      saving: false,
    }),
  )
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

// One platform, one rule. The stored rules are checked on both the value the
// enricher reads (target_value) and the name the row would take, because a rule
// renamed or retargeted in Desk can carry one without the other.
function platformTakenBy(row, platform) {
  const ruleName = socialRuleName(platform)

  return (socialRules.data || []).find(
    (rule) =>
      rule.name !== row.name &&
      (rule.target_value === platform || rule.rule_name === ruleName),
  )
}

function rowOptions(row) {
  return ConfirmDelete({
    isConfirmingDelete,
    onConfirmDelete: () => deleteRow(row),
  })
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

  // A pattern that doesn't compile is flagged wherever it was typed, on a stored
  // row or a new one, so leaving the box shows the problem straight away.
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

  if (row.platform === row.savedPlatform && row.pattern === row.savedPattern) {
    return
  }

  return updateRow(row)
}

// A new row waits on screen until both boxes are filled -- half of one is not a
// rule, and the doctype would reject it anyway (rule_name and pattern are both
// required). Rule and pattern go in as one document, so a failed insert leaves
// nothing half-created behind.
async function insertRow(row) {
  if (!row.platform || !row.pattern) return

  // commitRow has already refused a platform another rule holds; the server's
  // own unique-rule_name error still lands in the catch below for anything this
  // list hasn't loaded (a rule added in another tab, an Industry rule).
  row.saving = true
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Enrichment Rule',
        rule_type: 'Social',
        target_value: row.platform,
        match_scope: 'HTML',
        enabled: 1,
        rule_name: socialRuleName(row.platform),
        patterns: [{ pattern: row.pattern, is_regex: 1 }],
      },
    })
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not add social rule'))
    return
  } finally {
    row.saving = false
  }

  toast.success(__('Social rule added successfully'))
  // The reload rebuilds every stored row, so the local one is dropped first and
  // the saved one takes its place rather than sitting beside it.
  localRows.value = localRows.value.filter((other) => other !== row)
  reloadRules()
}

// frappe.client.set_value can reach a child row by its own name, but it takes
// one field at a time -- a row where both boxes changed would be two saves and
// two chances to half-apply. Re-reading the doc and posting the whole thing back
// with frappe.client.save sends the complete patterns table in one request, so
// the pattern rows this form doesn't show ride along exactly as stored. The doc
// is re-read rather than reused from load so its `modified` is fresh and the
// save isn't rejected as a stale write.
async function updateRow(row) {
  const previousPlatform = row.savedPlatform
  const previousPattern = row.savedPattern

  row.saving = true
  try {
    const doc = await call('frappe.client.get', {
      doctype: 'CRM Enrichment Rule',
      name: row.name,
    })

    doc.target_value = row.platform

    // rule_name carries the platform, so it moves with it -- a rule switched
    // from linkedin to youtube would otherwise still read "Social: linkedin" in
    // Desk. Only rewritten when the platform actually changed, so a rule
    // hand-named in Desk survives an edit to its pattern.
    if (row.platform !== previousPlatform) {
      doc.rule_name = socialRuleName(row.platform)
    }

    const patternRows = doc.patterns || []
    const target = patternRows.find((entry) => Number(entry.is_regex) === 1)
    if (target) target.pattern = row.pattern
    else patternRows.push({ pattern: row.pattern, is_regex: 1 })
    doc.patterns = patternRows

    const saved = await call('frappe.client.save', { doc })

    patterns[row.name] = saved.patterns || []
    const split = splitPatterns(patterns[row.name])
    row.hidden = split.hidden
    row.savedPlatform = row.platform
    row.savedPattern = row.pattern
    toast.success(__('Social rule updated successfully'))

    // platformTakenBy reads socialRules.data, and target_value / rule_name have
    // just moved underneath it. Without this, switching a rule from linkedin to
    // github leaves the list still claiming linkedin is taken, and the next row
    // to ask for linkedin is refused against a rule that no longer holds it.
    reloadRules()
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not save social rule'))
    // Put the row back to what the server last confirmed, so the screen never
    // shows a value that isn't stored.
    row.platform = previousPlatform
    row.pattern = previousPattern
    row.error = ''
  } finally {
    row.saving = false
  }
}

// A row that was never inserted is only on screen, so dropping it is a local
// splice -- there is nothing to delete.
async function deleteRow(row) {
  if (!row.name) {
    localRows.value = localRows.value.filter((other) => other !== row)
    return
  }

  row.saving = true
  try {
    await call('frappe.client.delete', {
      doctype: 'CRM Enrichment Rule',
      name: row.name,
    })
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not delete social rule'))
    return
  } finally {
    row.saving = false
  }

  toast.success(__('Social rule deleted successfully'))
  delete patterns[row.name]
  reloadRules()
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

// Keystrokes in a typed box land here instead of in the doc, so a half-typed
// number is never autosaved and never counts as a change. The value is folded
// into the doc when the box is committed (blur or Enter) or when Save is
// pressed. Toggles skip this -- a Switch has no in-between state.
const pending = reactive({})

// The master switch gates everything under it, so those rows read as disabled
// until enrichment is on: still visible, so you can see what turning it on would
// give you, but greyed and non-interactive.
const enrichmentOff = computed(() => !settings.doc?.enabled)

// Turning enrichment off puts the dependent inputs out of reach, so a half-typed
// value in one is dropped rather than left sitting in a greyed-out box -- or
// saved later by a Save button that still counted it as pending.
watch(enrichmentOff, (off) => {
  if (off) clearPending()
})

function clearPending() {
  Object.keys(pending).forEach((key) => delete pending[key])
}

// What the Save button is for: a doc the autosave has not caught up with, a
// typed box that hasn't been committed yet, or a social rule row in the same
// state. Toggles normally leave nothing behind here, so on a quiet page the
// button stays disabled.
const hasUnsavedChanges = computed(() => {
  if (!settings.doc) return false
  if (settings.isDirty) return true

  if (
    pending.max_pages !== undefined &&
    Number(pending.max_pages) !== settings.doc.max_pages
  ) {
    return true
  }

  return rows.value.some(isRowPending)
})

// Every save of the settings doc funnels through here, so there is exactly one
// submit and one toast per save. frappe-ui's save already rolls `doc` back to
// its pre-submit snapshot if the request fails, so dropping the pending
// keystrokes alongside it leaves the last saved value on screen.
function submitSettings(message) {
  settings.save
    .submit(null, {
      onSuccess: () => toast.success(message),
      onError: (err) => {
        toast.error(err.messages?.[0] || __('Could not save'))
        clearPending()
      },
    })
    // onError above is the handler; submit() rethrows on top of it, and an
    // unguarded rejection would only surface as console noise.
    .catch(() => {})
}

// A Switch hands us a Boolean, but Check fields come back from the server as
// 0/1 -- so write that shape back, or the doc would differ from originalDoc on
// every load. Every other fieldtype (max_pages is an Int) is saved as given.
function update(fieldname, value) {
  const isCheck = typeof value === 'boolean'
  settings.doc[fieldname] = isCheck ? (value ? 1 : 0) : value

  submitSettings(
    isCheck
      ? value
        ? __('Setting enabled successfully')
        : __('Setting disabled successfully')
      : __('Setting updated successfully'),
  )
}

// Folds the typed number into the doc, returning false if it was refused. The
// number input reports a string, and an emptied box reports '', so anything that
// isn't a positive whole number is rejected: saving 0 would leave the crawler
// fetching no pages at all. Dropping the pending value snaps the box back to the
// stored one, which is now what the input is bound to.
//
// No upper bound: nothing in crm/domain_enrichment clamps max_pages, so the UI
// doesn't invent a ceiling the backend doesn't have.
function applyMaxPages() {
  if (pending.max_pages === undefined) return true

  const pages = Number(pending.max_pages)

  if (!Number.isInteger(pages) || pages < 1) {
    toast.error(__('Max pages must be a whole number of 1 or more'))
    delete pending.max_pages
    return false
  }

  delete pending.max_pages
  settings.doc.max_pages = pages
  return true
}

// The Save button, a committed typed box, and the Rules tab all land here, so
// one press flushes whatever either tab is holding. Rule rows autosave on their
// own; this catches the one the pointer never left.
function save() {
  // A save is already in flight: its spinner is on the button, and a second
  // submit would race the first and toast twice. This also covers Enter
  // followed by the blur it causes.
  if (settings.save.loading) return
  if (!applyMaxPages()) return

  rows.value.filter(isRowPending).forEach((row) => commitRow(row))

  if (!settings.isDirty) return

  submitSettings(__('Settings updated successfully'))
}
</script>
