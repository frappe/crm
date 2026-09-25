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
          <EnrichmentRuleSection
            :title="__('Social profile rules')"
            :subtitle="
              __('Allow users to enrich leads when a website is available.')
            "
            :add-label="__('Add Social')"
            :loading="socialLoading"
            :error="socialResource.list.error"
            :error-message="__('Could not load social rules')"
            :count="socialRows.length"
            empty-name="Social Rules"
            :empty-title="__('No social rules found')"
            :empty-description="
              __('Add one to tell enrichment which profile links to look for.')
            "
            empty-icon="share-2"
            @add="addSocialRule"
            @retry="retrySocial"
          >
            <div
              v-for="row in socialRows"
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
                  :class="row.error ? invalidInputClass : ''"
                  @update:model-value="(value) => onPatternInput(row, value)"
                  @blur="commitSocialRow(row)"
                  @keyup.enter="commitSocialRow(row)"
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
              <EnrichmentRuleMenu @delete="deleteSocialRule(row)" />
            </div>
          </EnrichmentRuleSection>

          <EnrichmentRuleSection
            class="mt-8"
            :title="__('Industry rules')"
            :subtitle="
              __('Allow users to enrich leads when a website is available.')
            "
            :add-label="__('Add Industry')"
            :loading="industryLoading"
            :error="industryResource.list.error"
            :error-message="__('Could not load industry rules')"
            :count="industryRows.length"
            empty-name="Industry Rules"
            :empty-title="__('No industry rules found')"
            :empty-description="
              __(
                'Add one to tell enrichment which keywords point at which industry.',
              )
            "
            empty-icon="briefcase"
            @add="addIndustryRule"
            @retry="retryIndustry"
          >
            <div
              v-for="row in industryRows"
              :key="row.key"
              class="flex items-start gap-2"
            >
              <Link
                doctype="CRM Industry"
                :value="row.industry"
                :placeholder="__('Industry')"
                class="w-40 shrink-0"
                :class="row.enabled ? '' : 'opacity-60'"
                @change="(value) => onIndustryChange(row, value)"
              />
              <div
                class="flex-1 min-w-0"
                :class="row.enabled ? '' : 'opacity-60'"
              >
                <FormControl
                  :model-value="row.keywords"
                  type="text"
                  :placeholder="__('Keywords')"
                  :class="row.error ? invalidInputClass : ''"
                  @update:model-value="(value) => onKeywordsInput(row, value)"
                  @blur="commitIndustryRow(row)"
                  @keyup.enter="commitIndustryRow(row)"
                />
                <ErrorMessage
                  v-if="row.error"
                  class="mt-1"
                  :message="row.error"
                />
                <!-- Same affordance the Social rows use for the patterns they
                     don't show: here it is the rows the comma-separated box
                     can't safely round-trip (regexes, keywords with a comma). -->
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
              <div
                class="w-24 shrink-0"
                :class="row.enabled ? '' : 'opacity-60'"
              >
                <FormControl
                  :model-value="row.weight"
                  type="number"
                  step="0.1"
                  min="0"
                  :placeholder="__('Weight')"
                  :class="row.weightError ? invalidInputClass : ''"
                  @update:model-value="(value) => onWeightInput(row, value)"
                  @blur="commitIndustryRow(row)"
                  @keyup.enter="commitIndustryRow(row)"
                />
                <ErrorMessage
                  v-if="row.weightError"
                  class="mt-1"
                  :message="row.weightError"
                />
              </div>
              <Badge
                v-if="!row.enabled"
                :label="__('Disabled')"
                theme="gray"
                variant="subtle"
                size="sm"
                class="mt-1 shrink-0"
              />
              <EnrichmentRuleMenu @delete="deleteIndustryRule(row)" />
            </div>
          </EnrichmentRuleSection>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  createDocumentResource,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Select,
  Switch,
  Tabs,
  toast,
  Tooltip,
} from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import EnrichmentRuleMenu from '@/components/Settings/Enrichment/EnrichmentRuleMenu.vue'
import EnrichmentRuleSection from '@/components/Settings/Enrichment/EnrichmentRuleSection.vue'
import { useIndustryRules } from '@/components/Settings/Enrichment/useIndustryRules'
import { useSocialRules } from '@/components/Settings/Enrichment/useSocialRules'
import { computed, reactive, ref, watch } from 'vue'

// The red border a FormControl gets while its value is refused. Named here
// because every rule row wears it and the arbitrary-variant selector is a
// mouthful to repeat.
const invalidInputClass =
  '[&_input]:!border-outline-red-2 [&_input]:focus:!border-outline-red-2'

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

// Both rule lists are set up here rather than inside a section component: the
// Tabs panel is unmounted while the General tab is open (reka-ui's TabsContent
// defaults to unmountOnHide), so a half-filled row or a pending edit would be
// thrown away on a tab switch if it lived in the panel's own component.
const {
  rows: socialRows,
  pendingRows: socialPendingRows,
  loading: socialLoading,
  resource: socialResource,
  retry: retrySocial,
  addRow: addSocialRule,
  deleteRow: deleteSocialRule,
  commitRow: commitSocialRow,
  platformOptions,
  onPlatformChange,
  onPatternInput,
} = useSocialRules()

const {
  rows: industryRows,
  pendingRows: industryPendingRows,
  loading: industryLoading,
  resource: industryResource,
  retry: retryIndustry,
  addRow: addIndustryRule,
  deleteRow: deleteIndustryRule,
  commitRow: commitIndustryRow,
  onIndustryChange,
  onKeywordsInput,
  onWeightInput,
} = useIndustryRules()

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
// typed box that hasn't been committed yet, or a rule row in the same state.
// Toggles normally leave nothing behind here, so on a quiet page the button
// stays disabled.
const hasUnsavedChanges = computed(() => {
  if (!settings.doc) return false
  if (settings.isDirty) return true

  if (
    pending.max_pages !== undefined &&
    Number(pending.max_pages) !== settings.doc.max_pages
  ) {
    return true
  }

  return Boolean(
    socialPendingRows.value.length || industryPendingRows.value.length,
  )
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
// own; this catches the one the pointer never left, in both rule sections.
function save() {
  // A save is already in flight: its spinner is on the button, and a second
  // submit would race the first and toast twice. This also covers Enter
  // followed by the blur it causes.
  if (settings.save.loading) return
  if (!applyMaxPages()) return

  socialPendingRows.value.forEach((row) => commitSocialRow(row))
  industryPendingRows.value.forEach((row) => commitIndustryRow(row))

  if (!settings.isDirty) return

  submitSettings(__('Settings updated successfully'))
}
</script>
