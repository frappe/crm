<template>
  <SettingsLayoutBase
    :title="__('Preferences')"
    :description="
      __(
        'Choose how you want to use the application by setting your preferences.',
      )
    "
  >
    <template #content>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Appearance') }}
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-4 my-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Theme') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Switch between light, dark, or system theme') }}
            </span>
          </div>
          <ThemeSwitcher
            :logo="brand.logo || CRMLogo"
            :name="brand.name || 'CRM'"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import ThemeSwitcher from '@/components/Settings/ThemeSwitcher.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { getSettings } from '@/stores/settings'

const { brand } = getSettings()
</script>
