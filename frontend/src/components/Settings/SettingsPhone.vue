<!-- CRM Settings on a phone: a full-screen list of pages; a page opens over it with Back. -->
<template>
  <Teleport to="body">
    <div
      v-if="showSettings"
      class="fixed inset-0 z-40 flex flex-col bg-surface-base text-ink-gray-8"
      role="dialog"
      aria-modal="true"
      :aria-label="__('Settings')"
    >
      <template v-if="!page">
        <header
          class="flex h-12 shrink-0 items-center gap-1 border-b border-outline-gray-1 px-1.5"
        >
          <Button
            variant="ghost"
            icon="lucide-x"
            :aria-label="__('Close settings')"
            @click="showSettings = false"
          />
          <h1 class="flex-1 truncate text-lg-medium text-ink-gray-9">
            {{ __('Settings') }}
          </h1>
        </header>
        <div class="min-h-0 flex-1 overflow-y-auto overscroll-y-contain pb-8">
          <button
            type="button"
            class="flex w-full items-center gap-3 border-b border-outline-gray-1 p-4 text-left hover:bg-surface-gray-1"
            @click="openPage(profilePage)"
          >
            <Avatar
              :label="user.full_name"
              :image="user.user_image"
              size="2xl"
            />
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="truncate text-lg-semibold text-ink-gray-9">
                {{ user.full_name }}
              </span>
              <span class="truncate text-sm text-ink-gray-5">
                {{
                  [user.email || user.name, roleLabel]
                    .filter(Boolean)
                    .join(' · ')
                }}
              </span>
            </span>
            <span
              class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4"
              aria-hidden="true"
            />
          </button>
          <section
            v-for="group in phoneGroups"
            :key="group.label"
            class="flex flex-col pt-4"
          >
            <h2 class="px-4 pb-1 text-sm text-ink-gray-5">
              {{ __(group.label) }}
            </h2>
            <button
              v-for="item in group.items"
              :key="item.label"
              type="button"
              class="flex h-12 items-center gap-3 px-4 text-left hover:bg-surface-gray-1"
              @click="openPage(item)"
            >
              <span
                class="flex size-5 shrink-0 items-center justify-center text-ink-gray-6"
              >
                <Icon :icon="item.icon" class="size-4" />
              </span>
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
                {{ __(item.label) }}
              </span>
              <span
                class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4"
                aria-hidden="true"
              />
            </button>
          </section>
          <div
            v-if="desktopOnlyPages.length"
            class="mx-4 mt-5 flex gap-3 rounded-6 bg-surface-gray-1 p-3"
          >
            <span
              class="lucide-monitor mt-0.5 size-4 shrink-0 text-ink-gray-5"
              aria-hidden="true"
            />
            <p class="text-p-sm text-ink-gray-6">
              {{ __('On a computer: {0}.', [desktopOnlyPages.join(', ')]) }}
            </p>
          </div>
        </div>
      </template>

      <template v-else>
        <header
          class="flex h-12 shrink-0 items-center gap-1 border-b border-outline-gray-1 pl-1.5 pr-3"
        >
          <Button
            variant="ghost"
            icon="lucide-chevron-left"
            :aria-label="__('Back')"
            @click="back"
          />
          <h1 class="min-w-0 flex-1 truncate text-lg-medium text-ink-gray-9">
            {{ subpage?.title() || __(page.label) }}
          </h1>
          <div id="settings-phone-actions" class="flex shrink-0 gap-2" />
        </header>
        <div class="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <component :is="page.component" :key="page.label" />
        </div>
        <DiscardSaveBar
          v-if="saveBar?.isDirty()"
          :count="saveBar.count?.() || 0"
          :saving="Boolean(saveBar.saving?.())"
          @discard="saveBar.discard()"
          @save="saveBar.save()"
        />
      </template>
    </div>
  </Teleport>
</template>

<script setup>
import DiscardSaveBar from '@/components/DiscardSaveBar.vue'
import Icon from '@/components/Icon.vue'
import { useSettingsTabs } from '@/components/Settings/settingsTabs'
import { provideSettingsPhone } from '@/components/Settings/settingsPhone'
import { providePhonePickers, useBackClose } from '@/composables/phone'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { Avatar, Button } from 'frappe-ui'
import { computed, watch } from 'vue'

const ROLE_LABELS = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
}

const { tabs, user } = useSettingsTabs()
const { subpage, saveBar } = provideSettingsPhone()
providePhonePickers()

const pages = computed(() => tabs.value.flatMap((tab) => tab.items))
const profilePage = computed(() => pages.value[0])
const phoneGroups = computed(() =>
  tabs.value
    .map((tab) => ({
      ...tab,
      items: tab.items.filter(
        (item) => item.phone !== false && item !== profilePage.value,
      ),
    }))
    .filter((tab) => tab.items.length),
)
const desktopOnlyPages = computed(() =>
  pages.value.filter((item) => item.phone === false).map((item) => item.label),
)
// A desktop-only page asked for by name (onboarding, a link) shows the list.
const page = computed(() =>
  pages.value.find(
    (item) => item.label === activeSettingsPage.value && item.phone !== false,
  ),
)
const roleLabel = computed(() => ROLE_LABELS[user.value.role] || '')

useBackClose(
  () => showSettings.value,
  () => (showSettings.value = false),
)
useBackClose(
  () => showSettings.value && Boolean(page.value),
  () => (activeSettingsPage.value = ''),
)
useBackClose(
  () => Boolean(subpage.value),
  () => subpage.value?.back(),
)

watch(showSettings, (open) => !open && (activeSettingsPage.value = ''))

function openPage(item) {
  activeSettingsPage.value = item.label
}

function back() {
  if (subpage.value) return subpage.value.back()
  activeSettingsPage.value = ''
}
</script>
