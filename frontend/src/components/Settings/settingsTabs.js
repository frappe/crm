import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideNetwork from '~icons/lucide/network'
import LucideWorkflow from '~icons/lucide/workflow'
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
import BookingPagesSettings from '@/components/Settings/BookingPages/BookingPagesSettings.vue'
import AppMenuSettings from '@/components/Settings/AppMenu/AppMenuSettings.vue'
import FormsSettings from '@/components/Settings/Forms/FormsSettings.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import EnrichmentSettings from '@/components/Settings/Enrichment/EnrichmentSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import WorkflowAutomationPage from '@/components/Settings/WorkflowAutomations/WorkflowAutomationPage.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import { usersStore } from '@/stores/users'
import { isWhatsAppInstalled } from '@/composables/whatsapp'
import AssignmentRulePage from '@/components/Settings/AssignmentRules/AssignmentRulePage.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import LucideZap from '~icons/lucide/zap'
import SlaConfig from '@/components/Settings/Sla/SlaConfig.vue'

import { Avatar } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'

/**
 * The groups and pages of CRM Settings. `tabs` holds what this user may see.
 * `phone: false` marks pages that are desktop-only for now.
 */
export function useSettingsTabs() {
  const { isManager, getUser } = usersStore()
  const user = computed(() => getUser() || {})

  const allTabs = computed(() => {
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
            phone: false,
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
            phone: false,
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
        // managers see every item; sales users only their booking pages
        items: [
          {
            label: __('Workflow Automations'),
            phone: false,
            icon: LucideWorkflow,
            component: markRaw(WorkflowAutomationPage),
            condition: () => isManager(),
          },
          {
            label: __('Assignment Rules'),
            phone: false,
            icon: markRaw(h(SettingsIcon2, { class: 'rotate-90' })),
            component: markRaw(AssignmentRulePage),
            condition: () => isManager(),
          },
          {
            label: __('SLA Policies'),
            phone: false,
            icon: markRaw(h(ShieldCheck)),
            component: markRaw(SlaConfig),
            condition: () => isManager(),
          },
          {
            label: __('Forms'),
            phone: false,
            component: markRaw(FormsSettings),
            icon: markRaw(LucideTextCursorInput),
            condition: () => isManager(),
          },
          {
            label: __('Booking Pages'),
            icon: CalendarIcon,
            component: markRaw(BookingPagesSettings),
          },
          {
            label: __('Enrichment'),
            component: markRaw(EnrichmentSettings),
            icon: markRaw(LucideZap),
            condition: () => isManager(),
          },
        ],
      },
      {
        label: __('Customization'),
        items: [
          {
            label: __('App menu'),
            phone: false,
            component: markRaw(AppMenuSettings),
            icon: 'menu',
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
            condition: () => isWhatsAppInstalled.value && isManager(),
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

    return _tabs
  })

  const isVisible = (entry) => !entry.condition || entry.condition()

  const tabs = computed(() =>
    allTabs.value
      .filter(isVisible)
      .map((tab) => ({ ...tab, items: tab.items.filter(isVisible) })),
  )

  return { allTabs, tabs, user }
}
