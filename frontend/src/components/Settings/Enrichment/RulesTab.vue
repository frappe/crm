<template>
  <div ref="root" class="flex-1 flex flex-col overflow-y-auto">
    <div
      v-if="!enabled"
      class="mt-3 rounded bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-6"
    >
      {{ __('Enrichment is off. These rules apply once it is turned on.') }}
    </div>
    <EnrichmentRuleSection
      :title="__('Social profile rules')"
      :add-label="__('Add social rule')"
      :columns="[__('Platform'), __('Pattern')]"
      :errors="socialErrors()"
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
      :truncated="social.truncated"
      @add="social.addRow"
      @retry="social.load"
    >
      <div
        v-for="row in social.rows"
        :key="row.key"
        class="group/row flex flex-col"
      >
        <div class="flex items-start gap-2">
          <!-- Messages are listed under the section; the border marks the field. -->
          <FormControl
            :model-value="row.platform"
            type="text"
            :placeholder="__('Platform')"
            :disabled="social.saving || row.removed"
            class="w-40 shrink-0"
            :class="{ [INVALID]: row.platformError }"
            :data-invalid="row.platformError ? '' : undefined"
            @update:model-value="(value) => social.onPlatformInput(row, value)"
            @blur="social.checkRow(row)"
          />
          <div class="flex-1 min-w-0">
            <!-- Monospace so regex patterns are easier to read. -->
            <FormControl
              :model-value="row.pattern"
              type="text"
              :placeholder="__('e.g. mastodon\\.social/@\\w+')"
              :disabled="social.saving || row.removed"
              class="[&_input]:font-mono"
              :class="{ [INVALID]: row.patternError }"
              :data-invalid="row.patternError ? '' : undefined"
              @update:model-value="(value) => social.onPatternInput(row, value)"
              @blur="social.checkRow(row)"
            />
            <Tooltip v-if="row.hidden.length" :text="row.hidden.join('  |  ')">
              <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                {{
                  __('+{0} more pattern(s) on this rule', [row.hidden.length])
                }}
              </div>
            </Tooltip>
          </div>
          <!-- Only flips the row; the header Update saves it. The slot stays
               on blank rows so the column doesn't shift. -->
          <div class="w-8 shrink-0">
            <Switch
              v-if="!social.isRowBlank(row)"
              size="sm"
              class="mt-1.5"
              :class="SWITCH_OFF_HOVER"
              :model-value="row.enabled"
              :disabled="social.saving || row.removed"
              @update:model-value="social.toggleEnabled(row)"
            />
          </div>
          <!-- Left visible on touch, which has no hover to reveal it -->
          <div
            class="shrink-0 transition-opacity [&:has(:focus-visible)]:opacity-100 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover/row:opacity-100"
          >
            <Button
              variant="ghost"
              theme="red"
              icon="lucide-trash-2"
              :tooltip="__('Delete')"
              :disabled="social.saving || row.removed"
              @click="social.deleteRow(row)"
            />
          </div>
        </div>
      </div>
    </EnrichmentRuleSection>

    <div class="h-px border-t border-outline-elevation-2" />

    <EnrichmentRuleSection
      class="mt-4"
      :title="__('Industry rules')"
      :add-label="__('Add industry rule')"
      :columns="[__('Industry'), __('Keywords')]"
      :errors="industryErrors()"
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
      :truncated="industry.truncated"
      @add="industry.addRow"
      @retry="industry.load"
    >
      <div
        v-for="row in industry.rows"
        :key="row.key"
        class="group/row flex flex-col"
      >
        <div class="flex items-start gap-2">
          <div class="w-40 shrink-0">
            <div
              :class="{ [INVALID]: row.industryError }"
              :data-invalid="row.industryError ? '' : undefined"
            >
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
            </div>
            <div v-if="row.newIndustry" class="mt-1 text-p-sm text-ink-gray-5">
              {{ __('New industry, created on save') }}
            </div>
          </div>
          <div class="flex-1 min-w-0">
            <FormControl
              :model-value="row.keywords"
              type="text"
              :placeholder="__('Keywords, comma separated')"
              :disabled="industry.saving || row.removed"
              :class="{ [INVALID]: row.keywordsError }"
              :data-invalid="row.keywordsError ? '' : undefined"
              @update:model-value="
                (value) => industry.onKeywordsInput(row, value)
              "
              @blur="industry.checkRow(row)"
            />
            <!-- Regexes and keywords containing commas can't round-trip the
                 box, so they're listed here. -->
            <Tooltip v-if="row.hidden.length" :text="row.hidden.join('  |  ')">
              <div class="mt-1 w-fit text-p-sm text-ink-gray-5">
                {{
                  __('+{0} more keyword(s) on this rule', [row.hidden.length])
                }}
              </div>
            </Tooltip>
          </div>
          <!-- Slot stays on blank rows so the column doesn't shift. -->
          <div class="w-8 shrink-0">
            <Switch
              v-if="!industry.isRowBlank(row)"
              size="sm"
              class="mt-1.5"
              :class="SWITCH_OFF_HOVER"
              :model-value="row.enabled"
              :disabled="industry.saving || row.removed"
              @update:model-value="industry.toggleEnabled(row)"
            />
          </div>
          <!-- Left visible on touch, which has no hover to reveal it -->
          <div
            class="shrink-0 transition-opacity [&:has(:focus-visible)]:opacity-100 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover/row:opacity-100"
          >
            <Button
              variant="ghost"
              theme="red"
              icon="lucide-trash-2"
              :tooltip="__('Delete')"
              :disabled="industry.saving || row.removed"
              @click="industry.deleteRow(row)"
            />
          </div>
        </div>
      </div>
    </EnrichmentRuleSection>
  </div>
</template>

<script setup>
import { Button, FormControl, Switch, Tooltip } from 'frappe-ui'
import { ref } from 'vue'
import Link from '@/components/Controls/Link.vue'
import EnrichmentRuleSection from './EnrichmentRuleSection.vue'

// Rule state lives in the parent because reka-ui's TabsContent unmounts hidden
// panels by default.
const props = defineProps({
  // The rules stay editable while enrichment is off; this only shows the note.
  enabled: { type: Boolean, default: true },
  social: { type: Object, required: true },
  industry: { type: Object, required: true },
})

// frappe-ui's Switch hovers an off track with a fixed gray-400, which goes
// near-white in dark mode; use the themed equivalents instead.
const SWITCH_OFF_HOVER =
  '[&_[role=switch][data-state=unchecked]:enabled:hover]:bg-surface-gray-5 [&_[role=switch][data-state=unchecked]:enabled:active]:bg-surface-gray-6'

// Recolours the existing 1px border (input, or the picker's trigger button) so
// the row doesn't move; the message is listed under the section.
const INVALID =
  '[&_input]:!border-outline-red-3 [&_button]:!border-outline-red-3'

// Errors are listed under the section, so each names its rule; a row with no
// name yet goes by its position.
// Every error is listed, since a border alone can't say what's wrong; save
// failures mark no field, so they follow the field errors.
function rowErrors(rows, label, fields) {
  const fieldErrors = []
  const serverErrors = []
  rows.forEach((row, index) => {
    const name = label(row) || __('Row {0}', [index + 1])
    fields.forEach((field) => {
      if (row[field]) fieldErrors.push(__('{0}: {1}', [name, row[field]]))
    })
    if (row.serverError) {
      serverErrors.push(__('{0}: {1}', [name, row.serverError]))
    }
  })
  return [...fieldErrors, ...serverErrors]
}

function socialErrors() {
  return rowErrors(props.social.rows, (row) => row.platform.trim(), [
    'platformError',
    'patternError',
  ])
}

function industryErrors() {
  return rowErrors(props.industry.rows, (row) => row.industry, [
    'industryError',
    'keywordsError',
  ])
}

const root = ref(null)

// Called by the header Update when validation fails. The marker can land on
// the wrapper or, through FormControl's attrs, on the input itself.
function focusFirstError() {
  const marked = root.value?.querySelector('[data-invalid]')
  if (!marked) return
  const field = marked.querySelector('input, button') || marked
  field.scrollIntoView({ block: 'center' })
  field.focus({ preventScroll: true })
}

defineExpose({ focusFirstError })
</script>
