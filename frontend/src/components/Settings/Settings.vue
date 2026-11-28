<template>
  <SettingsPhone v-if="isPhone" />
  <Dialog
    v-else
    v-model:open="showSettings"
    :size="'5xl'"
    :dismissible="!disableSettingModalOutsideClick"
    bare
    @close="activeSettingsPage = ''"
  >
    <template #default>
      <Dialog.Title class="sr-only">{{ __('Settings') }}</Dialog.Title>
      <div class="flex h-[calc(100vh_-_8rem)] bg-surface-gray-1">
        <div
          ref="sidebarContainer"
          class="flex flex-col m-1 rounded-l-6 w-56 shrink-0 bg-surface-gray-1 overflow-y-auto"
        >
          <template v-for="(tab, i) in tabs" :key="tab.label">
            <div v-if="!tab.hideLabel && i != 0" class="mx-1 mb-0.5 mt-[5px]" />
            <div
              v-if="!tab.hideLabel"
              class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-xs-medium text-ink-gray-5 transition-all duration-300 ease-in-out sticky top-0 z-10 bg-surface-gray-1"
            >
              <span>{{ __(tab.label) }}</span>
            </div>
            <nav class="space-y-[3px] px-1">
              <SidebarItem
                v-for="item in tab.items"
                :key="item.label"
                :label="__(item.label)"
                :data-page="item.label"
                :active="activeTab?.label == item.label"
                class="w-full"
                :class="
                  activeTab?.label != item.label && 'hover:!bg-surface-gray-3'
                "
                @click="activeSettingsPage = item.label"
              >
                <template #prefix>
                  <Icon :icon="item.icon" class="size-4 text-ink-gray-7" />
                </template>
              </SidebarItem>
            </nav>
          </template>
        </div>
        <div
          class="flex flex-col flex-1 overflow-y-auto bg-surface-elevation-2"
        >
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import SettingsPhone from '@/components/Settings/SettingsPhone.vue'
import Icon from '@/components/Icon.vue'
import { useSettingsTabs } from '@/components/Settings/settingsTabs'
import {
  showSettings,
  activeSettingsPage,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { isPhone } from '@/composables/phone'
import { Dialog, SidebarItem } from 'frappe-ui'
import { ref, watch, nextTick } from 'vue'

const { allTabs, tabs } = useSettingsTabs()

const activeTab = ref(tabs.value[0].items[0])
const sidebarContainer = ref(null)

function setActiveTab(tabName) {
  const pages = tabs.value.flatMap((tab) => tab.items)
  activeTab.value =
    pages.find((page) => page.label === tabName) ||
    nextVisiblePage(tabName, pages) ||
    pages[0]
}

// A page the user cannot see opens the first one they can see after it.
function nextVisiblePage(tabName, pages) {
  const order = allTabs.value.flatMap((tab) =>
    tab.items.map((item) => item.label),
  )
  const start = order.indexOf(tabName)
  if (!tabName || start === -1) return null
  return order
    .slice(start + 1)
    .map((label) => pages.find((page) => page.label === label))
    .find(Boolean)
}

// Scroll the settings sidebar so the active page is in view (e.g. when opened
// deep-linked from onboarding, so the user sees where they landed).
function scrollActiveIntoView() {
  nextTick(() => {
    const el = sidebarContainer.value?.querySelector(
      `[data-page="${activeTab.value?.label}"]`,
    )
    el?.scrollIntoView({ block: 'nearest' })
  })
}

watch(activeSettingsPage, (activePage) => {
  setActiveTab(activePage)
  scrollActiveIntoView()
})
</script>
