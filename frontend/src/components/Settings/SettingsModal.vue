<template>
  <Dialog v-model="show" :options="{ size: '5xl' }">
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="px-2 pt-2 text-lg font-semibold">
            {{ __('Settings') }}
          </h1>
          <nav class="mt-3 space-y-1">
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
          </nav>
          <div
            class="mb-2 mt-3 flex cursor-pointer gap-1.5 px-1 text-base font-medium text-gray-600 transition-all duration-300 ease-in-out"
          >
            <span>{{ __('Integrations') }}</span>
          </div>
          <nav class="space-y-1">
            <SidebarLink
              v-for="i in integrations"
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
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import TwilioSettings from '@/components/Settings/TwilioSettings.vue'
import FieldsLayout from '@/components/Settings/FieldsLayout.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { isWhatsappInstalled } from '@/composables/settings'
import { Dialog, FeatherIcon } from 'frappe-ui'
import { ref, markRaw, computed, h } from 'vue'

const show = defineModel()

let tabs = [
  {
    label: 'Profile',
    icon: ContactsIcon,
    component: markRaw(ProfileSettings),
  },
  {
    label: 'Fields Layout',
    icon: h(FeatherIcon, { name: 'grid' }),
    component: markRaw(FieldsLayout),
  },
]

let integrations = computed(() => {
  let items = [
    {
      label: 'Twilio',
      icon: PhoneIcon,
      component: markRaw(TwilioSettings),
    },
  ]

  if (isWhatsappInstalled.value) {
    items.push({
      label: 'WhatsApp',
      icon: WhatsAppIcon,
      component: markRaw(WhatsAppSettings),
    })
  }

  return items
})

const activeTab = ref(tabs[0])
</script>
