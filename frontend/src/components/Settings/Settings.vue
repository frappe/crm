<template>
  <Dialog
    v-model:open="showSettings"
    :size="'5xl'"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
    @close="
      activeSettingsPage = '';
      searchQuery = '';
    "
  >
    <template #body>
      <div class="flex h-[calc(100vh_-_8rem)] bg-surface-gray-1">
        <div
          class="flex flex-col m-1 rounded-l-lg w-56 shrink-0 bg-surface-gray-1 overflow-y-auto"
        >
          <!-- Search Bar -->
          <div class="sticky top-0 z-20 bg-surface-sidebar p-2">
            <input
              v-model="searchQuery"
              :placeholder="__('Search settings...')"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm focus:outline-none focus:ring-0 focus:border-outline-gray-4"
            />
          </div>

          <!-- No Results -->
          <div
            v-if="filteredTabs.length === 0"
            class="p-4 text-sm text-ink-gray-5"
          >
            {{ __('No settings found.') }}
          </div>

          <!-- Settings List -->
          <template v-else v-for="(tab, i) in filteredTabs" :key="tab.label">
            <div
              v-if="!tab.hideLabel && i != 0"
              class="mx-1 mb-0.5 mt-[5px]"
            />

            <div
              v-if="!tab.hideLabel"
              class="h-7.5 px-2 py-[7px] my-[3px] flex gap-1.5 text-xs-medium text-ink-gray-5 sticky top-0 z-10 bg-surface-gray-1"
            >
              <span>{{ __(tab.label) }}</span>
            </div>

            <nav class="space-y-[3px] px-1">
              <SidebarLink
                v-for="item in tab.items"
                :key="item.label"
                :icon="item.icon"
                :label="__(item.label)"
                class="w-full"
                :class="
                  activeTab?.label == item.label
                    ? 'bg-surface-elevation-3 shadow-sm hover:bg-surface-elevation-3'
                    : 'hover:bg-surface-gray-3'
                "
                @click="activeSettingsPage = item.label"
              />
            </nav>
          </template>
        </div>

        <div
          class="flex flex-col flex-1 overflow-y-auto bg-surface-elevation-2"
        >
          <component
            :is="activeTab.component"
            v-if="activeTab"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideNetwork from '~icons/lucide/network'
import MonitorCogIcon from '~icons/lucide/monitor-cog'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import SlidersIcon from '@/components/Icons/SlidersIcon.vue'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import Users from '@/components/Settings/Users.vue'
import Hierarchy from '@/components/Settings/Hierarchy/Hierarchy.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import DefaultsSettings from '@/components/Settings/DefaultsSettings.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import CalendarSettings from '@/components/Settings/CalendarSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import FormsSettings from '@/components/Settings/Forms/FormsSettings.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { usersStore } from '@/stores/users'
import {
  showSettings,
  activeSettingsPage,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import { Dialog, Avatar } from 'frappe-ui'
import { ref, markRaw, computed, watch, h } from 'vue'
import AssignmentRulePage from './AssignmentRules/AssignmentRulePage.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import SlaConfig from './Sla/SlaConfig.vue'

const { isManager, getUser } = usersStore()

const user = computed(() => getUser() || {})

const searchQuery = ref('')

const tabs = computed(() => {
  let _tabs = [
    {
      label: __('User Configuration'),
      items: [
        {
          label: __('Profile'),
          icon: () =>
            h(Avatar, {
              size: 'xs',
              label: user.value.full_name,
              image: user.value.user_image,
            }),
          component: markRaw(ProfilePage),
        },
        {
          label: __('Preferences'),
          icon: SlidersIcon,
          component: markRaw(PreferencesSettings),
        },
      ],
    },
    {
      label: __('System Configuration'),
      items: [
        {
          label: __('General'),
          component: markRaw(GeneralSettings),
          icon: SettingsIcon,
        },
        {
          label: __('Dashboard'),
          component: markRaw(DashboardSettings),
          icon: LucideLayoutDashboard,
        },
        {
          label: __('Defaults'),
          component: markRaw(DefaultsSettings),
          icon: MonitorCogIcon,
        },
        {
          label: __('Brand'),
          icon: SparkleIcon,
          component: markRaw(BrandSettings),
        },
        {
          label: __('Calendar'),
          icon: CalendarIcon,
          component: markRaw(CalendarSettings),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('User Management'),
      items: [
        {
          label: __('Users'),
          icon: 'user',
          component: markRaw(Users),
          condition: () => isManager(),
        },
        {
          label: __('Invite User'),
          icon: 'user-plus',
          component: markRaw(InviteUserPage),
          condition: () => isManager(),
        },
        {
          label: __('Sales Hierarchy'),
          icon: LucideNetwork,
          component: markRaw(Hierarchy),
          condition: () => isManager(),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('Email'),
      items: [
        {
          label: __('Accounts'),
          icon: Email2Icon,
          component: markRaw(EmailConfig),
          condition: () => isManager(),
        },
        {
          label: __('Templates'),
          icon: EmailTemplateIcon,
          component: markRaw(EmailTemplatePage),
        },
      ],
    },
    {
      label: __('Automation & Rules'),
      items: [
        {
          label: __('Assignment Rules'),
          icon: markRaw(h(SettingsIcon2, { class: 'rotate-90' })),
          component: markRaw(AssignmentRulePage),
        },
        {
          label: __('SLA Policies'),
          icon: markRaw(h(ShieldCheck)),
          component: markRaw(SlaConfig),
        },
        {
          label: __('Forms'),
          component: markRaw(FormsSettings),
          icon: markRaw(LucideTextCursorInput),
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('Customization'),
      items: [
        {
          label: __('Home Actions'),
          component: markRaw(HomeActions),
          icon: 'home',
        },
      ],
      condition: () => isManager(),
    },
    {
      label: __('Integrations', null, 'FCRM'),
      items: [
        {
          label: __('Telephony'),
          icon: PhoneIcon,
          component: markRaw(TelephonyPage),
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
        {
          label: __('Lead Syncing'),
          icon: 'refresh-cw',
          component: markRaw(LeadSyncSourcePage),
          condition: () => isManager(),
        },
      ],
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

function getMatchScore(label, query) {
  const text = label.toLowerCase()

  // Exact beginning of label
  if (text.startsWith(query)) return 3

  // Beginning of any word
  if (text.split(/\s+/).some(word => word.startsWith(query))) return 2

  // Anywhere in label
  if (text.includes(query)) return 1

  return 0
}

const filteredTabs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  if (!query) {
    return tabs.value
  }

  return tabs.value
    .map((tab) => {
      // If section title matches, keep the entire section
      const sectionScore = getMatchScore(tab.label, query)

      if (sectionScore > 0) {
        return {
          ...tab,
          maxScore: sectionScore,
        }
      }

      const items = tab.items
        .map((item) => ({
          ...item,
          score: getMatchScore(item.label, query),
        }))
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score)

      return {
        ...tab,
        items,
        maxScore: items.length
          ? Math.max(...items.map((item) => item.score))
          : 0,
      }
    })
    .filter((tab) => tab.items.length > 0)
    .sort((a, b) => b.maxScore - a.maxScore)
})

const activeTab = ref(tabs.value[0].items[0])

function setActiveTab(tabName) {
  const items = filteredTabs.value.flatMap((tab) => tab.items)

  const selected =
    items.find((item) => item.label === tabName) ||
    items[0] ||
    null

  activeTab.value = selected
  activeSettingsPage.value = selected?.label || ''
}

watch(activeSettingsPage, (activePage) => {
  setActiveTab(activePage)
})

watch(filteredTabs, (newTabs) => {
  if (!newTabs.length) {
    activeTab.value = null
    activeSettingsPage.value = ''
    return
  }

  const visibleItems = newTabs.flatMap((tab) => tab.items)

  if (!visibleItems.find((item) => item.label === activeTab.value?.label)) {
    activeTab.value = visibleItems[0]
    activeSettingsPage.value = visibleItems[0].label
  }
})
</script>
