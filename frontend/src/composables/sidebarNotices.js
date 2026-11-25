import {
  useCloudSettings,
  isCloudSettingsAvailable,
} from '@/composables/cloudSettings'
import { useDemoData } from '@/composables/demoData'
import { useTrialCard } from '@/composables/trialCard'
import { usersStore } from '@/stores/users'
import { trialCardContent } from '@/utils/trialCard'
import { useTelemetry } from '@framework/ui/telemetry'
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

const URGENT_DAYS = 3
const LEVELS = { gray: 1, blue: 1, amber: 2, red: 3 }

/**
 * The notices behind the icon beside the avatar: the trial, the demo-site
 * signup and the sample data, each in `SidebarCard`'s shape. `level` is the
 * most urgent one's: 'none', 'info', 'soon' or 'urgent'.
 */
export function useSidebarNotices() {
  const { capture } = useTelemetry()
  const { isManager } = usersStore()
  const { isDemoDataCreated, clearDemoData } = useDemoData()
  const cloudTrial = useCloudTrialNotice(capture)
  const siteTrial = useSiteTrialNotice(capture)

  const notices = computed(() =>
    [
      cloudTrial.value,
      siteTrial.value,
      window.is_demo_site && signupNotice(capture),
      isManager() && isDemoDataCreated.value && sampleDataNotice(clearDemoData),
    ].filter(Boolean),
  )

  const level = computed(() => {
    const highest = Math.max(0, ...notices.value.map((n) => LEVELS[n.theme]))
    return ['none', 'info', 'soon', 'urgent'][highest]
  })

  return { notices, level }
}

/** The trial on a Frappe Cloud site that has Cloud Settings. */
function useCloudTrialNotice(capture) {
  const { trial, dismiss } = useTrialCard()
  const { opening, open } = useCloudSettings()

  return computed(() => {
    if (!trial.value) return null
    const content = trialCardContent(trial.value)
    return {
      key: 'cloud-trial',
      theme: content.theme,
      title: content.title,
      description: content.description,
      dismissible: content.dismissible,
      onDismiss: dismiss,
      action: {
        label: content.action,
        loading: opening.value,
        onClick: () => {
          capture('upgrade_plan_from_trial_banner')
          open()
        },
      },
    }
  })
}

/** The trial on an older Frappe Cloud site, which has no Cloud Settings. */
function useSiteTrialNotice(capture) {
  const enabled = window.is_fc_site && !isCloudSettingsAvailable()
  const site = createResource({
    url: 'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
    cache: 'current_site_info_data',
    auto: enabled,
  })

  return computed(() => {
    const info = site.data
    const daysLeft = daysUntil(info?.trial_end_date)
    if (!enabled || !info?.plan?.is_trial_plan || daysLeft <= 0) return null
    return {
      key: 'site-trial',
      theme: daysLeft <= URGENT_DAYS ? 'amber' : 'gray',
      title:
        daysLeft === 1
          ? __('Your trial ends tomorrow')
          : __('Your trial ends in {0} days', [String(daysLeft)]),
      description: __('Upgrade to a paid plan for uninterrupted services.'),
      dismissible: false,
      action: {
        label: __('Upgrade plan'),
        onClick: () => {
          capture('upgrade_plan_from_trial_banner')
          window.open(
            `${info.base_url}/dashboard/sites/${info.site_name}`,
            '_blank',
          )
        },
      },
    }
  })
}

function daysUntil(date) {
  if (!date) return 0
  return Math.ceil((new Date(date).getTime() - Date.now()) / 86400000)
}

function signupNotice(capture) {
  return {
    key: 'signup',
    theme: 'gray',
    title: __('Loved the demo?'),
    description: __('Try Frappe CRM for free with a 14-day trial.'),
    dismissible: false,
    action: {
      label: __('Sign up now'),
      onClick: () => {
        window.open('https://frappecloud.com/crm/signup', '_blank')
        capture('signup_from_demo_site')
      },
    },
  }
}

function sampleDataNotice(clearDemoData) {
  return {
    key: 'sample-data',
    theme: 'gray',
    title: __('Your CRM has sample data'),
    description: __(
      "Clear it when you're ready to add your own leads and deals.",
    ),
    dismissible: false,
    action: { label: __('Clear sample data'), onClick: clearDemoData },
  }
}
