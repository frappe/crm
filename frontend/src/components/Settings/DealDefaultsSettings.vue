<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Deal Defaults') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Configure default behavior when creating new deals',
          )
        }}
      </p>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default Choose Existing Organization') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'When creating a new deal, the "Choose Existing Organization" switch will be checked by default',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            size="sm"
            v-model="defaultChooseExistingOrganization"
            @update:modelValue="saveDefaultChooseExistingOrganization"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default Choose Existing Contact') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'When creating a new deal, the "Choose Existing Contact" switch will be checked by default',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            size="sm"
            v-model="defaultChooseExistingContact"
            @update:modelValue="saveDefaultChooseExistingContact"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getSettings } from '@/stores/settings'
import { Switch, toast } from 'frappe-ui'
import { computed } from 'vue'

const { _settings: settings } = getSettings()

// Convert numeric values (0/1) to boolean for Switch component
const defaultChooseExistingOrganization = computed({
  get: () => Boolean(settings.doc.default_choose_existing_organization),
  set: (value) => {
    settings.doc.default_choose_existing_organization = value ? 1 : 0
  },
})

const defaultChooseExistingContact = computed({
  get: () => Boolean(settings.doc.default_choose_existing_contact),
  set: (value) => {
    settings.doc.default_choose_existing_contact = value ? 1 : 0
  },
})

function saveDefaultChooseExistingOrganization(newValue) {
  settings.save.submit(null, {
    onSuccess: () => {
      // Reload settings to ensure all components get the updated values
      settings.reload()
      toast.success(
        newValue
          ? __('Default choose existing organization enabled')
          : __('Default choose existing organization disabled'),
      )
    },
    onError: (error) => {
      // Revert on error
      defaultChooseExistingOrganization.value = !newValue
      toast.error(__('Failed to save setting: ') + error.message)
    },
  })
}

function saveDefaultChooseExistingContact(newValue) {
  settings.save.submit(null, {
    onSuccess: () => {
      // Reload settings to ensure all components get the updated values
      settings.reload()
      toast.success(
        newValue
          ? __('Default choose existing contact enabled')
          : __('Default choose existing contact disabled'),
      )
    },
    onError: (error) => {
      // Revert on error
      defaultChooseExistingContact.value = !newValue
      toast.error(__('Failed to save setting: ') + error.message)
    },
  })
}
</script>
