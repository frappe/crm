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
        :label="__('Save')"
        variant="solid"
        :loading="saving"
        :disabled="!hasUnsavedChanges"
        @click="save"
      />
    </template>
    <template #content>
      <!-- frappe-ui's tab list has px-5 and no prop to change it; pl-0 removes
           only its left padding so "General" starts at the title's edge. -->
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

// frappe-ui's Tabs is index-based; `value` rides along on each tab so the panels
// key off a stable id rather than a translated label.
const tabIndex = ref(0)

const tabOptions = [
  { label: __('General'), value: 'general' },
  { label: __('Rules'), value: 'rules' },
]

// Both rule lists are set up here rather than inside RulesTab: the Tabs panel
// is unmounted while the other tab is open, so rows held in the panel would be
// thrown away on a tab switch. reactive() unwraps the composables' refs so the
// tab can read them as plain values.
const social = reactive(useSocialRules())
const industry = reactive(useIndustryRules())

// Mirrors MAX_PAGES_LIMIT in crm/domain_enrichment/config.py -- the Settings
// controller rejects anything outside 1..20 on save.
const MAX_PAGES_LIMIT = 20

// Keystrokes in the Maximum pages box land here instead of in the doc, so a
// half-typed number never counts as the stored one. It is folded into the doc
// on Save.
const maxPages = ref(undefined)
const maxPagesError = ref('')

watch(maxPages, () => (maxPagesError.value = ''))

// Turning enrichment off hides Maximum pages, but a half-typed value in it is
// kept in maxPages so it is back when enrichment is turned on again. While
// hidden it is left out of the dirty check, validation and Save, so a Save
// can't write -- or refuse over -- a value the admin can no longer see.
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

// Drives both the "Not Saved" badge and the Save button. A rule that failed to
// save is still changed, so the badge only clears once every part went through.
const hasUnsavedChanges = computed(
  () =>
    settingsDirty.value ||
    social.dirtyRows.length > 0 ||
    industry.dirtyRows.length > 0,
)

// A Switch hands us a Boolean, but Check fields come back from the server as
// 0/1 -- so write that shape back, or the doc would differ from originalDoc on
// every load.
function toggle(fieldname, value) {
  settings.doc[fieldname] = value ? 1 : 0
}

// The number input reports a string, and an emptied box reports '', so anything
// that isn't a whole number in range is refused: saving 0 would leave the
// crawler fetching no pages at all. The ceiling mirrors the Settings controller;
// catching it here turns a server throw into an inline message.
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

// frappe-ui's save rolls `doc` back to its pre-submit snapshot if the request
// fails, so a failure leaves the last saved values on screen.
async function saveSettings() {
  if (pendingMaxPages.value !== undefined) {
    settings.doc.max_pages = Number(pendingMaxPages.value)
    maxPages.value = undefined
  }

  // The onError keeps frappe-ui's fallback handler from toasting a second time;
  // submit() still rethrows on top of it, which is what the catch is for.
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

// One press saves both tabs. Everything is validated first -- a row with a bad
// regex or a taken platform stops the whole Save before a single request -- then
// the settings single and both rule lists go out together.
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
