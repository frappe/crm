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
          <div class="text-lg-semibold text-ink-gray-8 py-3 px-2">
            {{ __('Social profile rules') }}
          </div>

          <div
            v-if="rulesLoading"
            class="flex flex-1 items-center justify-center"
          >
            <LoadingIndicator class="size-4" />
          </div>
          <div
            v-else-if="socialRules.list.error"
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
            v-else-if="!socialRules.data?.length"
            class="flex-1"
            name="Social Rules"
            :title="__('No social rules found')"
            :description="
              __('Social rules are created when enrichment is installed.')
            "
            icon="share-2"
          />
          <div v-else>
            <div class="flex items-center p-2 text-sm text-ink-gray-5">
              <div class="w-3/12">{{ __('Platform') }}</div>
              <div class="w-7/12">{{ __('Patterns') }}</div>
              <div class="w-2/12">{{ __('Status') }}</div>
            </div>
            <div class="h-px border-t mx-2 border-outline-elevation-2" />
            <template v-for="(rule, i) in socialRules.data" :key="rule.name">
              <div class="flex items-start py-3 px-2">
                <div
                  class="w-3/12 pr-4 text-p-base-medium text-ink-gray-7 truncate"
                >
                  {{ rule.target_value || rule.rule_name }}
                </div>
                <div class="w-7/12 pr-4 flex flex-col gap-1">
                  <div
                    v-for="(pattern, index) in patterns[rule.name]"
                    :key="index"
                    class="break-all font-mono text-xs text-ink-gray-5"
                  >
                    {{ pattern }}
                  </div>
                  <div
                    v-if="!patterns[rule.name]?.length"
                    class="text-p-sm text-ink-gray-4"
                  >
                    {{ __('No patterns') }}
                  </div>
                </div>
                <div class="w-2/12">
                  <Badge
                    :label="rule.enabled ? __('Enabled') : __('Disabled')"
                    :theme="rule.enabled ? 'green' : 'gray'"
                    variant="subtle"
                    size="sm"
                  />
                </div>
              </div>
              <hr v-if="socialRules.data.length !== i + 1" class="mx-2" />
            </template>
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
  FormControl,
  LoadingIndicator,
  Switch,
  Tabs,
  toast,
} from 'frappe-ui'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { computed, reactive, ref, watch } from 'vue'

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

// rule name -> list of pattern strings
const patterns = reactive({})
const patternsLoading = ref(false)

// createListResource keeps its fetch state on `.list`, not on the resource
// itself -- the patterns land after it, so the spinner has to cover both.
const rulesLoading = computed(
  () => socialRules.list.loading || patternsLoading.value,
)

// reload() rethrows on a second failure, and an unguarded rejection here would
// only show up as console noise -- the error state already renders the message.
function retry() {
  socialRules.reload().catch(() => {})
}

// get_list never returns child tables, so the patterns have to be fetched
// separately: one frappe.client.get per rule, which is what the rest of Settings
// already does for a single doc (see WorkflowAutomationDetail.vue). A handful of
// Social rules means a handful of parallel requests -- cheaper than adding a
// backend endpoint for a read-only list. createDocumentResource per rule was the
// other option, but a resource can't be created inside v-for: it would have to
// be built and cached outside the render, and its save/setValue machinery is
// dead weight in a list nothing can edit yet.
async function loadPatterns(rules) {
  if (!rules?.length) return

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
      patterns[doc.name] = (doc.patterns || []).map((row) => row.pattern)
    })
  } catch (err) {
    // A row with no patterns loaded reads as "No patterns", so say out loud that
    // the fetch failed rather than letting it look like an empty rule.
    toast.error(err.messages?.[0] || __('Could not load rule patterns'))
  } finally {
    patternsLoading.value = false
  }
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

// What the Save button is for: a doc the autosave has not caught up with, or a
// typed box that hasn't been committed yet. Toggles normally leave nothing
// behind here, so on a quiet page the button stays disabled.
const hasUnsavedChanges = computed(() => {
  if (!settings.doc) return false
  if (settings.isDirty) return true

  return (
    pending.max_pages !== undefined &&
    Number(pending.max_pages) !== settings.doc.max_pages
  )
})

// Every save on this page funnels through here, so there is exactly one submit
// and one toast per save. frappe-ui's save already rolls `doc` back to its
// pre-submit snapshot if the request fails, so dropping the pending keystrokes
// alongside it leaves the last saved value on screen.
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

// The Save button and a committed typed box both land here. When the Rules tab
// gains editing it flushes its own pending edits from this one function.
function save() {
  // A save is already in flight: its spinner is on the button, and a second
  // submit would race the first and toast twice. This also covers Enter
  // followed by the blur it causes.
  if (settings.save.loading) return
  if (!applyMaxPages()) return
  if (!settings.isDirty) return

  submitSettings(__('Settings updated successfully'))
}
</script>
