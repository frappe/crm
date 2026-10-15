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
    <div class="flex items-start justify-between px-8 pt-8 pb-4">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('WhatsApp') }}
          <Badge
            v-if="activeTab === 'advanced' && settingsPage?.isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="amber"
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

    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      class="flex-1 overflow-hidden [&>[data-slot=tab-panel]]:flex [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-col [&>[data-slot=tab-panel]]:overflow-auto"
    >
      <template #tab-panel="{ tab }">
        <div class="flex h-full flex-col px-8 py-5">
          <WhatsAppTemplateList
            v-if="tab.value === 'templates'"
            @edit="editTemplate"
          />
          <WhatsAppAccountList
            v-else-if="tab.value === 'accounts'"
            @edit="editAccount"
          />
          <SettingsPage
            v-else
            ref="settingsPage"
            doctype="WA Settings"
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
</script>

<style scoped>
/* frappe-ui bakes px-5 into the tab list; drop it so the labels and the
   underline line up with the header and the panel content. */
.wa-tabs :deep([role='tablist']) {
  padding-left: 0;
  padding-right: 0;
  margin-left: 2rem;
  margin-right: 2rem;
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