import { Avatar, createResource } from 'frappe-ui'
import { computed, markRaw, ref, h } from 'vue'
import CircleDollarSignIcon from '~icons/lucide/circle-dollar-sign'
import TrendingUpDownIcon from '~icons/lucide/trending-up-down'
import SparkleIcon from '@/components/Icons/SparkleIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import ERPNextIcon from '@/components/Icons/ERPNextIcon.vue'
import HelpdeskIcon from '@/components/Icons/HelpdeskIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import SettingsIcon2 from '@/components/Icons/SettingsIcon2.vue'
import Users from '@/components/Settings/Users.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import ProfileSettings from '@/components/Settings/ProfileSettings.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ERPNextSettings from '@/components/Settings/ERPNextSettings.vue'
import HelpdeskSettings from '@/components/Settings/HelpdeskSettings.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import CalendarSettings from '@/components/Settings/CalendarSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import ForecastingSettings from '@/components/Settings/ForecastingSettings.vue'
import CurrencySettings from '@/components/Settings/CurrencySettings.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import TelephonySettings from '@/components/Settings/TelephonySettings.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import AssignmentRulePage from '@/components/Settings/AssignmentRules/AssignmentRulePage.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import SlaConfig from '@/components/Settings/Sla/SlaConfig.vue'
import BusinessHolidayConfig from '@/components/Settings/BusinessHoliday/BusinessHolidayConfig.vue'
import Briefcase from '~icons/lucide/briefcase'
import { usersStore } from '@/stores/users'

export const whatsappEnabled = ref(false)
export const isWhatsappInstalled = ref(false)
createResource({
  url: 'crm.api.whatsapp.is_whatsapp_enabled',
  cache: 'Is Whatsapp Enabled',
  auto: true,
  onSuccess: (data) => {
    whatsappEnabled.value = Boolean(data)
  },
})
createResource({
  url: 'crm.api.whatsapp.is_whatsapp_installed',
  cache: 'Is Whatsapp Installed',
  auto: true,
  onSuccess: (data) => {
    isWhatsappInstalled.value = Boolean(data)
  },
})

export const callEnabled = ref(false)
export const twilioEnabled = ref(false)
export const exotelEnabled = ref(false)
export const defaultCallingMedium = ref('')
createResource({
  url: 'crm.integrations.api.is_call_integration_enabled',
  cache: 'Is Call Integration Enabled',
  auto: true,
  onSuccess: (data) => {
    twilioEnabled.value = Boolean(data.twilio_enabled)
    exotelEnabled.value = Boolean(data.exotel_enabled)
    defaultCallingMedium.value = data.default_calling_medium
    callEnabled.value = twilioEnabled.value || exotelEnabled.value
  },
})

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')

const { isManager, isTelephonyAgent, getUser } = usersStore()

const user = computed(() => getUser() || {})

export const settingsTabs = computed(() => {
  let _tabs = [
    {
      label: __('Personal Settings'),
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
      ],
    },
    {
      label: __('System Configuration'),
      items: [
        {
          label: __('Forecasting'),
          component: markRaw(ForecastingSettings),
          icon: TrendingUpDownIcon,
        },
        {
          label: __('Currency & Exchange Rate'),
          icon: CircleDollarSignIcon,
          component: markRaw(CurrencySettings),
        },
        {
          label: __('Brand Settings'),
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
      ],
      condition: () => isManager(),
    },
    {
      label: __('Email Settings'),
      items: [
        {
          label: __('Email Accounts'),
          icon: Email2Icon,
          component: markRaw(EmailConfig),
          condition: () => isManager(),
        },
        {
          label: __('Email Templates'),
          icon: EmailTemplateIcon,
          component: markRaw(EmailTemplatePage),
        },
      ],
    },
    {
      label: __('Automation & Rules'),
      items: [
        {
          label: __('Assignment rules'),
          icon: markRaw(h(SettingsIcon2, { class: 'rotate-90' })),
          component: markRaw(AssignmentRulePage),
        },
        {
          label: __('SLA Policies'),
          icon: markRaw(h(ShieldCheck)),
          component: markRaw(SlaConfig),
        },
        {
          label: __('Business Holidays'),
          icon: markRaw(Briefcase),
          component: markRaw(BusinessHolidayConfig),
        },
      ],
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
          component: markRaw(TelephonySettings),
          condition: () => isManager() || isTelephonyAgent(),
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
          label: __('Helpdesk'),
          icon: HelpdeskIcon,
          component: markRaw(HelpdeskSettings),
          condition: () => isManager(),
        },
        {
          label: __('Lead Syncing'),
          icon: 'refresh-cw',
          component: markRaw(LeadSyncSourcePage),
          condition: () => isManager(),
        },
      ],
      condition: () => isManager() || isTelephonyAgent(),
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

export function setSettingsActiveTab(tabName) {
  settingsActiveTab.value =
    (tabName &&
      settingsTabs.value
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.label === tabName)) ||
    settingsTabs.value[0].items[0]
}

export const settingsActiveTab = ref(settingsTabs.value[0].items[0])
