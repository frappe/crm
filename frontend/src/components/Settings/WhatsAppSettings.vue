<template>
  <!-- Adding an account is the same screen as editing one, just unsaved. -->
  <SettingsPage
    v-if="step === 'account'"
    :key="accountName || 'new'"
    doctype="WhatsApp Account"
    :name="accountName"
    :is-new="!accountName"
    :title="accountName || __('New Account')"
    :success-message="accountName ? 'Account updated' : 'Account created'"
    :back="showAccounts"
    class="p-6"
    @created="showAccounts"
  />
  <div v-else class="wa-tabs flex h-full flex-col text-ink-gray-8">
    <div class="flex items-start justify-between px-6 pt-8 pb-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('WhatsApp') }}
          <Badge
            v-if="tabIndex === 1 && settingsPage?.isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Connect WhatsApp Business accounts and configure the Meta Cloud API connection.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="tabIndex === 0"
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
          <WhatsAppAccountList
            v-if="tab.name === 'accounts'"
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
import { Tabs } from 'frappe-ui'
import { ref, useTemplateRef } from 'vue'

const tabs = [
  { name: 'accounts', label: __('Accounts') },
  { name: 'connection', label: __('Connection') },
]

const step = ref('home')
const accountName = ref('')
const tabIndex = ref(0)

const settingsPage = useTemplateRef('settingsPage')

function editAccount(name) {
  accountName.value = name
  step.value = 'account'
}

function addAccount() {
  accountName.value = ''
  step.value = 'account'
}

function showAccounts() {
  step.value = 'home'
  accountName.value = ''
  tabIndex.value = 0
}
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
