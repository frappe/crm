<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <div
      v-if="!enabled"
      class="mt-3 rounded bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-6"
    >
      {{ __('Enrichment is off. These rules apply once it is turned on.') }}
    </div>
    <EnrichmentRuleSection
      :title="__('Social profile rules')"
      :add-label="__('Add social rule')"
      :loading="social.loading"
      :error="social.error"
      :error-message="__('Could not load social rules')"
      :count="social.rows.length"
      empty-name="Social Rules"
      :empty-title="__('No social rules yet')"
      :empty-description="
        __('Add one to tell enrichment which profile links to look for.')
      "
      empty-icon="share-2"
      :has-more="social.hasMore"
      :loading-more="social.loadingMore"
      @add="social.addRow"
      @retry="social.load"
      @load-more="social.loadMore"
    >
      <div v-for="row in social.rows" :key="row.key" class="flex flex-col">
        <div class="flex items-start gap-2">
          <div class="w-40 shrink-0">
            <Autocomplete
              :ref="(el) => (platformBoxes[row.key] = el)"
              :model-value="row.platform"
              :options="platformOptions()"
              :placeholder="__('Platform')"
              variant="transparent"
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
            <!-- Autocomplete has no error prop, so the message sits below. -->
            <ErrorMessage
              v-if="row.platformError"
              class="mt-1"
              :message="row.platformError"
            />
          </div>
          <div class="flex-1 min-w-0">
            <!-- Monospace so regex patterns are easier to read. -->
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
          <!-- Only flips the row; the header Update saves it. -->
          <Switch
            v-if="!social.isRowBlank(row)"
            size="sm"
            class="mt-1.5 shrink-0"
            :model-value="row.enabled"
            :disabled="social.saving || row.removed"
            @update:model-value="social.toggleEnabled(row)"
          />
          <EnrichmentRuleMenu
            :blank="social.isRowBlank(row)"
            :disabled="social.saving || row.removed"
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

    <div class="h-px border-t border-outline-elevation-2" />

    <EnrichmentRuleSection
      class="mt-4"
      :title="__('Industry rules')"
      :add-label="__('Add industry rule')"
      :loading="industry.loading"
      :error="industry.error"
      :error-message="__('Could not load industry rules')"
      :count="industry.rows.length"
      empty-name="Industry Rules"
      :empty-title="__('No industry rules yet')"
      :empty-description="
        __('Add one to tell enrichment which keywords point at which industry.')
      "
      empty-icon="briefcase"
      :has-more="industry.hasMore"
      :loading-more="industry.loadingMore"
      @add="industry.addRow"
      @retry="industry.load"
      @load-more="industry.loadMore"
    >
      <div v-for="row in industry.rows" :key="row.key" class="flex flex-col">
        <div class="flex items-start gap-2">
          <div class="w-40 shrink-0">
            <Link
              doctype="CRM Industry"
              :value="row.industry"
              :placeholder="__('Industry')"
              variant="transparent"
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
          <div class="flex-1 min-w-0">
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
            <!-- Regexes and keywords containing commas can't round-trip the
                 box, so they're listed here. -->
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
          <Switch
            v-if="!industry.isRowBlank(row)"
            size="sm"
            class="mt-1.5 shrink-0"
            :model-value="row.enabled"
            :disabled="industry.saving || row.removed"
            @update:model-value="industry.toggleEnabled(row)"
          />
          <EnrichmentRuleMenu
            :blank="industry.isRowBlank(row)"
            :disabled="industry.saving || row.removed"
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
import { Button, ErrorMessage, FormControl, Switch, Tooltip } from 'frappe-ui'
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

// Rule state lives in the parent because reka-ui's TabsContent unmounts hidden
// panels by default.
const props = defineProps({
  // The rules stay editable while enrichment is off; this only shows the note.
  enabled: { type: Boolean, default: true },
  social: { type: Object, required: true },
  industry: { type: Object, required: true },
})

// Seeded platforms plus already-saved ones, so a custom one can be re-picked.
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

// Per-row search text, so "Add" can name it and stay disabled while empty.
const platformQuery = reactive({})
const platformBoxes = {}

function platformAddLabel(row) {
  const query = platformQuery[row.key]?.trim()
  return query ? __('Add "{0}"', [query]) : __('Add new')
}

// Autocomplete keeps its search text on close; clear it or reopening shows
// stale text.
function onPlatformAdd(row, close) {
  props.social.onPlatformCreate(row, platformQuery[row.key], close)
  if (platformBoxes[row.key]) platformBoxes[row.key].query = ''
  platformQuery[row.key] = ''
}

function onPlatformSelect(row, option) {
  if (!option?.value) return
  props.social.onPlatformInput(row, option.value)
  props.social.checkRow(row)
  // The pattern is still checked on Save.
  if (!row.pattern) row.patternError = ''
}
</script>
