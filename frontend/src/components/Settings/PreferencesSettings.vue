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
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Language & Time') }}
            </div>
          </div>
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Language') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Change language of the application') }}
            </span>
          </div>
          <Link
            v-model="language"
            doctype="Language"
            class="w-40"
            @update:modelValue="language = $event || user.language"
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
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import { ref, computed } from 'vue'

const { getUser } = usersStore()
const { brand } = getSettings()

const user = computed(() => getUser() || {})

const language = ref(user.value.language)
</script>
