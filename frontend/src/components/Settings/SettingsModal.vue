<template>
  <Dialog v-model="show" :options="{ size: '5xl' }">
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="mb-3 px-2 pt-2 text-lg font-semibold">
            {{ __('Settings') }}
          </h1>
          <div v-for="tab in tabs">
            <div
              v-if="!tab.hideLabel"
              class="mb-2 mt-3 flex cursor-pointer gap-1.5 px-1 text-base font-medium text-gray-600 transition-all duration-300 ease-in-out"
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
                    ? 'bg-white shadow-sm'
                    : 'hover:bg-gray-100'
                "
                @click="activeTab = i"
              />
            </nav>
          </div>
        </div>
        <div class="flex flex-1 flex-col overflow-y-auto">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import InviteMemberPage from '@/components/Settings/InviteMemberPage.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import TwilioSettings from '@/components/Settings/TwilioSettings.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { isWhatsappInstalled } from '@/composables/settings'
import { Dialog } from 'frappe-ui'
import { ref, markRaw, computed, h } from 'vue'

const show = defineModel()

const tabs = computed(() => {
  let _tabs = [
    {
      label: __('Settings'),
      hideLabel: true,
      items: [
        {
          label: __('Profile'),
          icon: ContactsIcon,
          component: markRaw(ProfileSettings),
        },
        {
          label: __('Invite Members'),
          icon: 'user-plus',
          component: markRaw(InviteMemberPage),
        },
      ],
    },
    {
      label: __('Integrations'),
      items: [
        {
          label: __('Twilio'),
          icon: PhoneIcon,
          component: markRaw(TwilioSettings),
        },
        {
          label: __('WhatsApp'),
          icon: WhatsAppIcon,
          component: markRaw(WhatsAppSettings),
          condition: () => isWhatsappInstalled.value,
        },
        {
          label: __('ERPNext'),
          icon: ERPNextIcon,
          component: markRaw(ERPNextSettings),
        },
      ],
    },
  ]

  return _tabs.map((tab) => {
    tab.items = tab.items.filter((item) => {
      if (item.condition) {
        return item.condition()
      }
      return true
    })
    return tab
  })
})

const activeTab = ref(tabs.value[0].items[0])
</script>
