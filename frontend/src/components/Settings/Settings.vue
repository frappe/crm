<template>
  <Dialog
    v-model="showSettings"
    :options="{ size: '5xl' }"
    @close="activeSettingsPage = ''"
  >
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex flex-col p-2 w-52 shrink-0 bg-surface-gray-2">
          <h1 class="px-2 pt-2 mb-3 text-lg font-semibold text-ink-gray-9">
            {{ __('Settings') }}
          </h1>
          <div v-for="tab in tabs">
            <div
              v-if="!tab.hideLabel"
              class="mb-2 mt-3 flex cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
            >
              <span>{{ __(tab.label) }}</span>
            </div>
            <nav class="space-y-1">
              <SidebarLink
                v-for="i in tab.items"
                :icon="i.icon"
                :label="__(i.label)"
                class="w-full"
                :class="
                  activeTab?.label == i.label
                    ? 'bg-surface-selected shadow-sm hover:bg-surface-selected'
                    : 'hover:bg-surface-gray-3'
                "
                @click="activeTab = i"
              />
            </nav>
          </div>
        </div>
        <div
          class="relative flex flex-col flex-1 overflow-y-auto bg-surface-modal"
        >
          <Button
            class="absolute right-5 top-5"
            variant="ghost"
            icon="x"
            @click="showSettings = false"
          />
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import InviteMemberPage from '@/components/Settings/InviteMemberPage.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import TelephonySettings from '@/components/Settings/TelephonySettings.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { usersStore } from '@/stores/users'
import {
  isWhatsappInstalled,
  showSettings,
  activeSettingsPage,
} from '@/composables/settings'
import { Dialog, Button, Avatar } from 'frappe-ui'
import { ref, markRaw, computed, watch, h } from 'vue'

const { isManager, isAgent, getUser } = usersStore()

const user = computed(() => getUser() || {})

const tabs = computed(() => {
  let _tabs = [
    {
      label: __('Settings'),
      hideLabel: true,
      items: [
        {
          label: __('Profile'),
          icon: () =>
            h(Avatar, {
              size: 'xs',
              label: user.value.full_name,
              image: user.value.user_image,
            }),
          component: markRaw(ProfileSettings),
        },
        {
          label: __('General'),
          icon: 'settings',
          component: markRaw(GeneralSettings),
          condition: () => isManager(),
        },
        {
          label: __('Invite Members'),
          icon: InviteIcon,
          component: markRaw(InviteMemberPage),
          condition: () => isManager(),
        },
        {
          label: __('Email Accounts'),
          icon: Email2Icon,
          component: markRaw(EmailConfig),
          condition: () => isManager(),
        },
      ],
    },
    {
      label: __('Integrations'),
      items: [
        {
          label: __('Telephony'),
          icon: PhoneIcon,
          component: markRaw(TelephonySettings),
          condition: () => isManager() || isAgent(),
        },
        {
          label: __('WhatsApp'),
          icon: WhatsAppIcon,
          component: markRaw(WhatsAppSettings),
          condition: () => isWhatsappInstalled.value && isManager(),
        },
        {
          label: __('ERPNext'),
          icon: ERPNextIcon,
          component: markRaw(ERPNextSettings),
          condition: () => isManager(),
        },
      ],
      condition: () => isManager() || isAgent(),
    },
  ]

  return _tabs.filter((tab) => {
    if (tab.condition && !tab.condition()) return false
    if (tab.items) {
      tab.items = tab.items.filter((item) => {
        if (item.condition && !item.condition()) return false
        return true
      })
    }
    return true
  })
})

const activeTab = ref(tabs.value[0].items[0])

function setActiveTab(tabName) {
  activeTab.value =
    (tabName &&
      tabs.value
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.label === tabName)) ||
    tabs.value[0].items[0]
}

watch(activeSettingsPage, (activePage) => setActiveTab(activePage))
</script>
