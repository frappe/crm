<template>
  <Dialog v-model="show" :options="{ size: '5xl' }">
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="px-2 pt-2 text-lg font-semibold">
            {{ __('Settings') }}
          </h1>
          <div class="mt-3 space-y-1">
            <SidebarLink
              v-for="tab in tabs"
              :icon="tab.icon"
              :label="__(tab.label)"
              class="w-full"
              :class="
                activeTab?.label == tab.label
                  ? 'bg-white shadow-sm'
                  : 'hover:bg-gray-100'
              "
              @click="activeTab = tab"
            />
          </div>
        </div>
        <div class="flex flex-1 flex-col overflow-y-auto p-12 pt-10">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ref, markRaw } from 'vue'
import { Dialog } from 'frappe-ui'
import SidebarLink from '@/components/SidebarLink.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import AgentSettings from '@/components/Settings/AgentSettings.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'

const show = defineModel()

let tabs = [
  {
    label: 'Profile',
    icon: ContactsIcon,
    component: markRaw(ProfileSettings),
  },
  {
    label: 'Agents',
    icon: LeadsIcon,
    component: markRaw(AgentSettings),
  },
]

const activeTab = ref(tabs[0])
</script>
