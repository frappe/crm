<template>
  <!-- Adding a record is the same screen as editing one, just unsaved. -->
  <WhatsAppTemplatePage
    v-if="step === 'template'"
    :key="templateName || 'new'"
    :name="templateName"
    :reference-doctype="templateReferenceDoctype"
    @back="showHome"
    @created="showHome"
  />
  <WhatsAppAccountPage
    v-else-if="step === 'account'"
    :key="accountName || 'new'"
    :name="accountName"
    @back="showHome"
    @created="showHome"
  />
  <div v-else class="wa-tabs flex h-full flex-col text-ink-gray-8">
    <div class="flex items-start justify-between px-6 pt-8 pb-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('WhatsApp') }}
          <Badge
            v-if="activeTab === 'advanced' && settingsPage?.isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Templates, accounts and the Meta Cloud API connection.') }}
        </p>
      </div>
      <Button
        v-if="activeTab === 'templates'"
        :label="__('New Template')"
        icon-left="lucide-plus"
        variant="solid"
        @click="newTemplate()"
      />
      <Button
        v-else-if="activeTab === 'accounts'"
        :label="__('Add Account')"
        icon-left="lucide-plus"
        variant="solid"
        @click="addAccount"
      />
      <Button
        v-else-if="settingsPage?.isDirty"
        :loading="settingsPage?.saving"
        :label="__('Save')"
        variant="solid"
        @click="settingsPage?.save()"
      />
    </div>

    <Tabs v-model="tabIndex" as="div" :tabs="tabs">
      <template #tab-panel="{ tab }">
        <div class="flex h-full flex-col px-6 py-5">
          <WhatsAppTemplateList
            v-if="tab.name === 'templates'"
            @edit="editTemplate"
          />
          <WhatsAppAccountList
            v-else-if="tab.name === 'accounts'"
            @edit="editAccount"
          />
          <SettingsPage
            v-else
            ref="settingsPage"
            doctype="WhatsApp Settings"
            :exclude-fields="['default_account']"
            embedded
            hideHeader
          />
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'
import WhatsAppAccountList from '@/components/Settings/WhatsAppAccountList.vue'
import WhatsAppAccountPage from '@/components/Settings/WhatsAppAccountPage.vue'
import WhatsAppTemplateList from '@/components/Settings/WhatsAppTemplateList.vue'
import WhatsAppTemplatePage from '@/components/Settings/WhatsAppTemplatePage.vue'
import { useBroadcast } from '@/composables/useBroadcast'
import { Tabs } from 'frappe-ui'
import { computed, ref, useTemplateRef } from 'vue'

// Templates first: they change far more often than the account or the connection.
const tabs = [
  { name: 'templates', label: __('Templates') },
  { name: 'accounts', label: __('Accounts') },
  { name: 'advanced', label: __('Advanced') },
]

const step = ref('home')
const tabIndex = ref(0)
const accountName = ref('')
const templateName = ref('')
const templateReferenceDoctype = ref('')

const settingsPage = useTemplateRef('settingsPage')
const { on } = useBroadcast()

const activeTab = computed(() => tabs[tabIndex.value]?.name)

function editAccount(name) {
  accountName.value = name
  step.value = 'account'
}

function addAccount() {
  accountName.value = ''
  step.value = 'account'
}

function editTemplate(name) {
  templateName.value = name
  templateReferenceDoctype.value = ''
  step.value = 'template'
}

function newTemplate(referenceDoctype = '') {
  templateName.value = ''
  templateReferenceDoctype.value = referenceDoctype
  step.value = 'template'
}

// Leaves the tab where it was, so closing a record lands on the list it came from.
function showHome() {
  step.value = 'home'
  accountName.value = ''
  templateName.value = ''
}

// The template picker on a document opens this page straight onto a new template.
on('whatsapp_template_page', (data) => {
  tabIndex.value = 0
  newTemplate(data?.reference_doctype || '')
})
</script>

<style scoped>
/* frappe-ui bakes px-5 into the tab list; drop it so the labels and the
   underline line up with the header and the panel content. */
.wa-tabs :deep([role='tablist']) {
  padding-left: 0;
  padding-right: 0;
  margin-left: 1.5rem;
  margin-right: 1.5rem;
}

/* reka-ui force-mounts every panel and marks the inactive ones `hidden`, but the
   `flex` utility frappe-ui puts on them outranks Tailwind's `[hidden]` rule, so
   they stay live flex items. Hide them, and let only the visible one take the
   leftover height — otherwise it splits the height with an empty sibling. */
.wa-tabs :deep([role='tabpanel'][data-state='inactive']) {
  display: none;
}

.wa-tabs :deep([role='tabpanel'][data-state='active']) {
  flex: 1 1 0%;
}
</style>
