<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <EnrichmentRuleSection
      :title="__('Social profile rules')"
      :subtitle="__('Allow users to enrich leads when a website is available.')"
      :add-label="__('Add Social')"
      :loading="social.loading"
      :error="social.error"
      :error-message="__('Could not load social rules')"
      :count="social.rows.length"
      empty-name="Social Rules"
      :empty-title="__('No social rules found')"
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
            <FormControl
              :model-value="row.platform"
              type="text"
              variant="outline"
              :placeholder="__('Platform')"
              :disabled="social.saving"
              :class="row.platformError ? invalidInputClass : ''"
              @update:model-value="
                (value) => social.onPlatformInput(row, value)
              "
              @blur="social.checkRow(row)"
            />
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
              variant="outline"
              :placeholder="__('Regex pattern')"
              :disabled="social.saving"
              class="[&_input]:font-mono"
              :class="row.patternError ? invalidInputClass : ''"
              @update:model-value="(value) => social.onPatternInput(row, value)"
              @blur="social.checkRow(row)"
            />
            <ErrorMessage
              v-if="row.patternError"
              class="mt-1"
              :message="row.patternError"
            />
            <Tooltip
              v-else-if="row.hidden.length"
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
            :disabled="social.saving"
            @toggle="social.toggleEnabled(row)"
            @delete="social.deleteRow(row)"
          />
        </div>
        <ErrorMessage
          v-if="row.serverError"
          class="mt-1"
          :message="row.serverError"
        />
      </div>
    </EnrichmentRuleSection>

    <EnrichmentRuleSection
      class="mt-8"
      :title="__('Industry rules')"
      :subtitle="__('Allow users to enrich leads when a website is available.')"
      :add-label="__('Add Industry')"
      :loading="industry.loading"
      :error="industry.error"
      :error-message="__('Could not load industry rules')"
      :count="industry.rows.length"
      empty-name="Industry Rules"
      :empty-title="__('No industry rules found')"
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
              variant="outline"
              :value="row.industry"
              :placeholder="__('Industry')"
              :disabled="industry.saving"
              @create="
                (value, close) => industry.onIndustryCreate(row, value, close)
              "
              @change="(value) => industry.onIndustryChange(row, value)"
            />
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
              variant="outline"
              :placeholder="__('Keywords, comma separated')"
              :disabled="industry.saving"
              :class="row.keywordsError ? invalidInputClass : ''"
              @update:model-value="
                (value) => industry.onKeywordsInput(row, value)
              "
              @blur="industry.checkRow(row)"
            />
            <ErrorMessage
              v-if="row.keywordsError"
              class="mt-1"
              :message="row.keywordsError"
            />
            <!-- Same affordance the Social rows use for the patterns they
                 don't show: here it is the rows the comma-separated box can't
                 safely round-trip (regexes, keywords with a comma). -->
            <Tooltip
              v-else-if="row.hidden.length"
              :text="row.hidden.join('  |  ')"
            >
              <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                {{
                  __('+{0} more pattern(s) on this rule', [row.hidden.length])
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
            :disabled="industry.saving"
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
import { Badge, ErrorMessage, FormControl, Tooltip } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import EnrichmentRuleMenu from './EnrichmentRuleMenu.vue'
import EnrichmentRuleSection from './EnrichmentRuleSection.vue'

// The rule lists themselves live in EnrichmentSettings.vue: the Tabs panel is
// unmounted while the General tab is open (reka-ui's TabsContent defaults to
// unmountOnHide), so edits held in this component would be thrown away on a
// tab switch. This only renders them and hands every change back to the
// composable that owns the row.
defineProps({
  social: { type: Object, required: true },
  industry: { type: Object, required: true },
})

// The red border a FormControl gets while its value is refused. Named here
// because every rule row wears it and the arbitrary-variant selector is a
// mouthful to repeat.
const invalidInputClass =
  '[&_input]:!border-outline-red-2 [&_input]:focus:!border-outline-red-2'
</script>
