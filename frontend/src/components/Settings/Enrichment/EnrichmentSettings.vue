<template>
  <SettingsLayoutBase
    :description="
      __('Set up enrichment availability and match website data to CRM fields.')
    "
  >
    <template #title>
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Enrichment Settings') }}
        <Badge
          v-if="hasUnsavedChanges"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </h2>
    </template>
    <template #header-actions>
      <Button
        :label="__('Update')"
        variant="solid"
        :loading="saving"
        :disabled="!hasUnsavedChanges"
        @click="save"
      />
    </template>
    <template #content>
      <!-- frappe-ui's tab list has px-5 and no prop for it; pl-0 aligns
           "General" with the title. -->
      <Tabs
        v-if="settings.doc"
        v-model="tabIndex"
        as="div"
        :tabs="tabOptions"
        class="h-full [&_[role='tablist']]:pl-0"
      >
        <template #tab-panel="{ tab }">
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
            :enabled="Boolean(settings.doc.enabled)"
            :social="social"
            :industry="industry"
          />
        </template>
      </Tabs>
      <div
        v-else-if="settings.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import {
  Badge,
  Button,
  createDocumentResource,
  LoadingIndicator,
  Tabs,
  toast,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import GeneralTab from './GeneralTab.vue'
import RulesTab from './RulesTab.vue'
import { useIndustryRules } from './useIndustryRules'
import { useSocialRules } from './useSocialRules'
import { computed, reactive, ref, watch } from 'vue'

const settings = createDocumentResource({
  doctype: 'CRM Enrichment Settings',
  name: 'CRM Enrichment Settings',
  auto: true,
})

// frappe-ui's Tabs is index-based; `value` gives panels a stable id instead of
// a translated label.
const tabIndex = ref(0)

const tabOptions = [
  { label: __('General'), value: 'general' },
  { label: __('Rules'), value: 'rules' },
]

// Owned here because the hidden tab panel is unmounted; reactive() unwraps the
// refs for the tab.
const social = reactive(useSocialRules())
const industry = reactive(useIndustryRules())

// Mirrors MAX_PAGES_LIMIT in crm/domain_enrichment/config.py; the controller
// rejects values outside 1..20.
const MAX_PAGES_LIMIT = 20

// Held apart from the doc so a half-typed number never counts as stored; folded
// in on Update.
const maxPages = ref(undefined)
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
function toggle(fieldname, value) {
  settings.doc[fieldname] = value ? 1 : 0
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
    settings.doc.max_pages = Number(pendingMaxPages.value)
    maxPages.value = undefined
  }

  // onError stops frappe-ui's fallback toast; submit() still rethrows, hence
  // the catch.
  let ok = true
  await settings.save
    .submit(null, {
      onError: (err) => {
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
    tabIndex.value = generalValid ? 1 : 0
    toast.error(__('Fix the highlighted fields before saving'))
    return
  }

  saving.value = true
  try {
    const results = await Promise.all([
      saveSettings(),
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
