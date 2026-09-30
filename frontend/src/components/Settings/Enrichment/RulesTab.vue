<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <EnrichmentRuleSection
      :title="__('Social profile rules')"
      :subtitle="
        __(
          'Find social profile links on the company website by matching them against each platform pattern.',
        )
      "
      :add-label="__('Add Social')"
      :loading="social.loading"
      :error="social.error"
      :error-message="__('Could not load social rules')"
      :count="social.rows.length"
      empty-name="Social Rules"
      :empty-description="
        __('Add one to tell enrichment which profile links to look for.')
      "
      empty-icon="share-2"
      @add="social.addRow"
      @retry="social.load"
    >
      <div v-for="row in social.rows" :key="row.key" class="flex flex-col">
        <div class="flex items-start gap-2">
          <div class="w-40 shrink-0" :class="row.enabled ? '' : 'opacity-60'">
            <Autocomplete
              :ref="(el) => (platformBoxes[row.key] = el)"
              :model-value="row.platform"
              :options="platformOptions()"
              :placeholder="__('Platform')"
              :disabled="social.saving || row.removed"
              @update:model-value="(option) => onPlatformSelect(row, option)"
              @update:query="(query) => (platformQuery[row.key] = query)"
            >
              <template #footer="{ close }">
                <Button
                  variant="ghost"
                  class="w-full !justify-start"
                  :label="platformAddLabel(row)"
                  :disabled="!platformQuery[row.key]?.trim()"
                  icon-left="lucide-plus"
                  @click="onPlatformAdd(row, close)"
                />
              </template>
            </Autocomplete>
            <!-- Autocomplete has no error prop, so its message is shown below it. -->
            <ErrorMessage
              v-if="row.platformError"
              class="mt-1"
              :message="row.platformError"
            />
          </div>
          <div class="flex-1 min-w-0" :class="row.enabled ? '' : 'opacity-60'">
            <FormControl
              :model-value="row.pattern"
              type="text"
              :placeholder="__('Regex pattern')"
              :disabled="social.saving || row.removed"
              class="[&_input]:font-mono"
              :error="row.patternError || undefined"
              @update:model-value="(value) => social.onPatternInput(row, value)"
              @blur="social.checkRow(row)"
            />
            <Tooltip
              v-if="!row.patternError && row.hidden.length"
              :text="row.hidden.join('  |  ')"
            >
              <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                {{
                  __('+{0} more pattern(s) on this rule', [row.hidden.length])
                }}
              </div>
            </Tooltip>
          </div>
          <!-- Shown only when the rule is off, the way HierarchyRow.vue marks a
               disabled user. Outside the dimmed columns so it stays readable;
               the switch that turns it back on is in the ⋯ menu. -->
          <Badge
            v-if="!row.enabled"
            :label="__('Disabled')"
            theme="gray"
            variant="subtle"
            size="sm"
            class="mt-1 shrink-0"
          />
          <EnrichmentRuleMenu
            :enabled="row.enabled"
            :blank="social.isRowBlank(row)"
            :disabled="social.saving || row.removed"
            @toggle="social.toggleEnabled(row)"
            @delete="social.deleteRow(row)"
          />
        </div>
        <ErrorMessage
          v-if="row.serverError"
          class="mt-1"
          :message="row.serverError"
        />
        <div
          v-else-if="
            row.platform.trim() &&
            !isKnownPlatform(row.platform) &&
            !row.platformError &&
            !row.patternError
          "
          class="mt-1 text-p-sm text-ink-gray-5"
        >
          {{
            __(
              'Links will be recorded on the enrichment run but not written to a field.',
            )
          }}
        </div>
      </div>
    </EnrichmentRuleSection>

    <div class="h-px border-t mx-2 border-outline-elevation-2" />

    <EnrichmentRuleSection
      class="mt-4"
      :title="__('Industry rules')"
      :subtitle="
        __(
          'Pick an industry by scoring the company website against the keywords on each rule. Weak or unclear matches are skipped.',
        )
      "
      :add-label="__('Add Industry')"
      :loading="industry.loading"
      :error="industry.error"
      :error-message="__('Could not load industry rules')"
      :count="industry.rows.length"
      empty-name="Industry Rules"
      :empty-description="
        __('Add one to tell enrichment which keywords point at which industry.')
      "
      empty-icon="briefcase"
      @add="industry.addRow"
      @retry="industry.load"
    >
      <div v-for="row in industry.rows" :key="row.key" class="flex flex-col">
        <div class="flex items-start gap-2">
          <div class="w-40 shrink-0" :class="row.enabled ? '' : 'opacity-60'">
            <Link
              doctype="CRM Industry"
              :value="row.industry"
              :placeholder="__('Industry')"
              :disabled="industry.saving || row.removed"
              @create="
                (value, close) => industry.onIndustryCreate(row, value, close)
              "
              @change="(value) => industry.onIndustryChange(row, value)"
            />
            <!-- Link has no error prop, so its message is shown below it. -->
            <ErrorMessage
              v-if="row.industryError"
              class="mt-1"
              :message="row.industryError"
            />
            <div
              v-else-if="row.newIndustry"
              class="mt-1 text-p-sm text-ink-gray-5"
            >
              {{ __('New industry, created on save') }}
            </div>
          </div>
          <div class="flex-1 min-w-0" :class="row.enabled ? '' : 'opacity-60'">
            <FormControl
              :model-value="row.keywords"
              type="text"
              :placeholder="__('Keywords, comma separated')"
              :disabled="industry.saving || row.removed"
              :error="row.keywordsError || undefined"
              @update:model-value="
                (value) => industry.onKeywordsInput(row, value)
              "
              @blur="industry.checkRow(row)"
            />
            <!-- Same affordance the Social rows use for the patterns they
                 don't show: here it is the rows the comma-separated box can't
                 safely round-trip (regexes, keywords with a comma). -->
            <Tooltip
              v-if="!row.keywordsError && row.hidden.length"
              :text="row.hidden.join('  |  ')"
            >
              <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                {{
                  __('+{0} more keyword(s) on this rule', [row.hidden.length])
                }}
              </div>
            </Tooltip>
          </div>
          <Badge
            v-if="!row.enabled"
            :label="__('Disabled')"
            theme="gray"
            variant="subtle"
            size="sm"
            class="mt-1 shrink-0"
          />
          <EnrichmentRuleMenu
            :enabled="row.enabled"
            :blank="industry.isRowBlank(row)"
            :disabled="industry.saving || row.removed"
            @toggle="industry.toggleEnabled(row)"
            @delete="industry.deleteRow(row)"
          />
        </div>
        <ErrorMessage
          v-if="row.serverError"
          class="mt-1"
          :message="row.serverError"
        />
      </div>
    </EnrichmentRuleSection>
  </div>
</template>

<script setup>
import { Badge, Button, ErrorMessage, FormControl, Tooltip } from 'frappe-ui'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { reactive } from 'vue'
import Link from '@/components/Controls/Link.vue'
import EnrichmentRuleMenu from './EnrichmentRuleMenu.vue'
import EnrichmentRuleSection from './EnrichmentRuleSection.vue'
import {
  SOCIAL_PLATFORMS,
  isKnownPlatform,
  normalizePlatform,
} from './useSocialRules'

// The rule lists themselves live in EnrichmentSettings.vue: the Tabs panel is
// unmounted while the General tab is open (reka-ui's TabsContent defaults to
// unmountOnHide), so edits held in this component would be thrown away on a
// tab switch. This only renders them and hands every change back to the
// composable that owns the row.
const props = defineProps({
  social: { type: Object, required: true },
  industry: { type: Object, required: true },
})

// Suggestions, not a whitelist: the seeded platforms plus any other platform a
// rule is already saved with, so one added earlier can be picked again. Anything
// else comes in through "Add new". Platforms outside SOCIAL_PLATFORMS are
// matched and recorded on the enrichment run, but mapper.py has no CRM field
// for them, so the row says so under it.
function platformOptions() {
  const options = [...SOCIAL_PLATFORMS]
  for (const row of props.social.rows) {
    const value = normalizePlatform(row.savedPlatform)
    if (value && !options.some((option) => option.value === value)) {
      options.push({ label: value, value })
    }
  }
  return options
}

// What is typed in each row's Platform search, keyed by row.key, so "Add"
// can name it and stays disabled until there is something to add.
const platformQuery = reactive({})
const platformBoxes = {}

function platformAddLabel(row) {
  const query = platformQuery[row.key]?.trim()
  return query ? __('Add "{0}"', [query]) : __('Add new')
}

// The Autocomplete keeps its search text when it closes, so it is cleared
// through the box too; otherwise reopening would show the old text under a
// disabled "Add new".
function onPlatformAdd(row, close) {
  props.social.onPlatformCreate(row, platformQuery[row.key], close)
  if (platformBoxes[row.key]) platformBoxes[row.key].query = ''
  platformQuery[row.key] = ''
}

// The Autocomplete hands back the whole option. A platform can't be blank, so
// an empty selection is ignored.
function onPlatformSelect(row, option) {
  if (!option?.value) return
  props.social.onPlatformInput(row, option.value)
  props.social.checkRow(row)
  // The pattern is still checked on Save.
  if (!row.pattern) row.patternError = ''
}
</script>
