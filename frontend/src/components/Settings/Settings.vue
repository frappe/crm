<template>
  <Dialog
    v-model="showSettings"
    :options="{ size: '5xl' }"
    @close="setSettingsActiveTab('')"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex flex-col p-1 w-52 shrink-0 bg-surface-gray-2">
          <h1 class="px-3 pt-3 pb-2 text-lg font-semibold text-ink-gray-8">
            {{ __('Settings') }}
          </h1>
          <div class="flex flex-col overflow-y-auto">
            <template v-for="tab in settingsTabs" :key="tab.label">
              <div
                v-if="!tab.hideLabel"
                class="py-[7px] px-2 my-1 flex cursor-pointer gap-1.5 text-base text-ink-gray-5 transition-all duration-300 ease-in-out"
              >
                <span>{{ __(tab.label) }}</span>
              </div>
              <nav class="space-y-1 px-1">
                <SidebarLink
                  v-for="i in tab.items"
                  :icon="i.icon"
                  :label="__(i.label)"
                  class="w-full"
                  :class="
                    settingsActiveTab?.label == i.label
                      ? 'bg-surface-selected shadow-sm hover:bg-surface-selected'
                      : 'hover:bg-surface-gray-3'
                  "
                  @click="setSettingsActiveTab(i.label)"
                />
              </nav>
            </template>
          </div>
        </div>
        <div class="flex flex-col flex-1 overflow-y-auto bg-surface-modal">
          <component
            :is="settingsActiveTab.component"
            v-if="settingsActiveTab"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SidebarLink from '@/components/SidebarLink.vue'
import {
  showSettings,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { Dialog } from 'frappe-ui'
import {
  setSettingsActiveTab,
  settingsActiveTab,
  settingsTabs,
} from '../../composables/settings'
</script>
