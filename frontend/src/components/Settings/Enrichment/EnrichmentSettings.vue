<template>
  <div class="enrichment-tabs flex h-full flex-col text-ink-gray-8">
    <div class="flex items-start justify-between px-8 pt-8 pb-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Enrichment Settings') }}
          <Badge
            v-if="hasUnsavedChanges"
            :label="__('Not Saved')"
            variant="subtle"
            theme="amber"
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
      <Button
        :label="__('Update')"
        variant="solid"
        :loading="saving"
        :disabled="!hasUnsavedChanges"
        @click="save"
      />
    </div>

    <Tabs
      v-if="settings.doc"
      v-model="activeTab"
      as="div"
      :tabs="tabOptions"
      class="flex-1 overflow-hidden [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-1"
    >
      <template #tab-panel="{ tab }">
        <div class="flex h-full flex-col overflow-y-auto px-8 py-5">
          <GeneralTab
            v-if="tab.value === 'general'"
            v-model:max-pages="maxPages"
            :doc="settings.doc"
            :max-pages-error="maxPagesError"
            :max-pages-limit="MAX_PAGES_LIMIT"
            @toggle="toggle"
          />
          <RulesTab
            v-else
            ref="rulesTab"
            :enabled="Boolean(settings.doc.enabled)"
            :social="social"
            :industry="industry"
          />
        </div>
      </template>
    </Tabs>
    <div
      v-else-if="settings.get.loading"
      class="flex items-center justify-center mt-[35%]"
    >
      <LoadingIndicator class="size-6" />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Badge,
  Button,
  createDocumentResource,
  LoadingIndicator,
  Tabs,
  toast,
  type FrappeResourceError,
} from 'frappe-ui'
import GeneralTab from './GeneralTab.vue'
import RulesTab from './RulesTab.vue'
import { useIndustryRules } from './useIndustryRules'
import { useSocialRules } from './useSocialRules'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import type { EnrichmentSettingsDoc } from './types'

const settings = createDocumentResource<EnrichmentSettingsDoc>({
  doctype: 'CRM Enrichment Settings',
  name: 'CRM Enrichment Settings',
  auto: true,
})

// frappe-ui's Tabs selects by `value`, a stable id instead of a translated
// label.
const activeTab = ref('general')

const tabOptions = [
  { label: __('General'), value: 'general' },
  { label: __('Rules'), value: 'rules' },
]

// Owned here because the hidden tab panel is unmounted; reactive() unwraps the
// refs for the tab.
const social = reactive(useSocialRules())
const industry = reactive(useIndustryRules())

const rulesTab = ref<InstanceType<typeof RulesTab> | null>(null)

// reka mounts a panel a few ticks after its tab is selected, so focus once
// the Rules tab's ref arrives instead of counting ticks.
let focusRulesError = false
watch(
  rulesTab,
  (tab) => {
    if (!tab || !focusRulesError) return
    focusRulesError = false
    tab.focusFirstError()
  },
  { flush: 'post' },
)

// Mirrors MAX_PAGES_LIMIT in crm/domain_enrichment/config.py; the controller
// rejects values outside 1..20.
const MAX_PAGES_LIMIT = 20

// Held apart from the doc so a half-typed number never counts as stored; folded
// in on Update.
const maxPages = ref<string | number | undefined>(undefined)
const maxPagesError = ref('')

watch(maxPages, () => (maxPagesError.value = ''))

// Kept while enrichment is off, but not validated or saved, so Save can't
// write or reject a value the admin can't see.
const pendingMaxPages = computed(() =>
  settings.doc?.enabled ? maxPages.value : undefined,
)

const saving = ref(false)

const settingsDirty = computed(() => {
  if (!settings.doc) return false
  if (settings.isDirty) return true

  return (
    pendingMaxPages.value !== undefined &&
    Number(pendingMaxPages.value) !== settings.doc.max_pages
  )
})

// A rule that failed to save stays dirty, so the badge only clears once
// everything went through.
const hasUnsavedChanges = computed(
  () =>
    settingsDirty.value ||
    social.dirtyRows.length > 0 ||
    industry.dirtyRows.length > 0,
)

// Check fields come back as 0/1; writing a Boolean would leave the doc
// permanently dirty.
function toggle(fieldname: 'enabled' | 'auto_enrich', value: boolean) {
  settings.doc![fieldname] = value ? 1 : 0
}

// The input reports strings ('' when emptied); 0 would crawl nothing, and over
// the limit the server throws.
function validateMaxPages() {
  if (pendingMaxPages.value === undefined) return true

  const pages = Number(pendingMaxPages.value)
  if (
    pendingMaxPages.value === '' ||
    !Number.isInteger(pages) ||
    pages < 1 ||
    pages > MAX_PAGES_LIMIT
  ) {
    maxPagesError.value = __(
      'Maximum pages must be a whole number between 1 and {0}',
      [MAX_PAGES_LIMIT],
    )
    return false
  }
  return true
}

// On failure frappe-ui rolls `doc` back to its pre-submit snapshot, leaving the
// saved values on screen.
async function saveSettings() {
  if (pendingMaxPages.value !== undefined) {
    settings.doc!.max_pages = Number(pendingMaxPages.value)
    maxPages.value = undefined
  }

  // onError stops frappe-ui's fallback toast; submit() still rethrows, hence
  // the catch.
  let ok = true
  await settings.save
    .submit(null, {
      onError: (err: FrappeResourceError) => {
        ok = false
        toast.error(err?.messages?.[0] || __('Could not save settings'))
      },
    })
    .catch(() => (ok = false))
  return ok
}

// Validate everything first so one bad row stops the whole Save before any
// request goes out.
async function save() {
  if (saving.value) return

  // Not short-circuited, so every tab gets its errors marked in one pass.
  const generalValid = validateMaxPages()
  const rulesValid = [social.validate(), industry.validate()].every(Boolean)

  if (!generalValid || !rulesValid) {
    // Onto the tab holding the error, so the message has somewhere to be seen.
    activeTab.value = generalValid ? 'rules' : 'general'
    toast.error(__('Fix the highlighted fields before saving'))
    if (generalValid) {
      if (rulesTab.value) {
        // Already on Rules: wait for the new red borders to render.
        await nextTick()
        rulesTab.value.focusFirstError()
      } else {
        focusRulesError = true
      }
    }
    return
  }

  saving.value = true
  try {
    // Skipped when unchanged, so a rules-only Save can't trip Settings
    // validation on a stored value the admin didn't touch.
    const results = await Promise.all([
      settingsDirty.value ? saveSettings() : true,
      social.save(),
      industry.save(),
    ])

    if (results.every(Boolean)) {
      toast.success(__('Settings updated successfully'))
    } else {
      toast.error(__('Some changes could not be saved'))
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
/* Same tab list alignment as WhatsAppSettings: frappe-ui bakes px-5 into it. */
.enrichment-tabs :deep([role='tablist']) {
  padding-left: 0;
  padding-right: 0;
  margin-left: 2rem;
  margin-right: 2rem;
}
</style>
