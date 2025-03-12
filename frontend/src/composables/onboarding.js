import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import { capture } from '@/telemetry'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { useStorage } from '@vueuse/core'
import { call } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, reactive, computed, markRaw } from 'vue'

let router

export const minimize = ref(false)

export const isOnboardingStepsCompleted = useStorage(
  'isOnboardingStepsCompleted',
  false,
)

const firstLead = ref('')
const firstDeal = ref('')

const steps = reactive([
  {
    name: 'create_first_lead',
    title: 'Create your first lead',
    icon: markRaw(LeadsIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      router.push({ name: 'Leads' })
    },
  },
  {
    name: 'invite_your_team',
    title: 'Invite your team',
    icon: markRaw(InviteIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      showSettings.value = true
      activeSettingsPage.value = 'Invite Members'
    },
  },
  {
    name: 'convert_lead_to_deal',
    title: 'Convert lead to deal',
    icon: markRaw(ConvertIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true

      let lead = await getFirstLead()

      if (lead) {
        router.push({ name: 'Lead', params: { leadId: lead } })
      } else {
        router.push({ name: 'Leads' })
      }
    },
  },
  {
    name: 'create_first_task',
    title: 'Create your first task',
    icon: markRaw(TaskIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#tasks',
        })
      } else {
        router.push({ name: 'Tasks' })
      }
    },
  },
  {
    name: 'create_first_note',
    title: 'Create your first note',
    icon: markRaw(NoteIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#notes',
        })
      } else {
        router.push({ name: 'Notes' })
      }
    },
  },
  {
    name: 'add_first_comment',
    title: 'Add your first comment',
    icon: markRaw(CommentIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#comments',
        })
      } else {
        router.push({ name: 'Leads' })
      }
    },
  },
  {
    name: 'send_first_email',
    title: 'Send email',
    icon: markRaw(EmailIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#emails',
        })
      } else {
        router.push({ name: 'Leads' })
      }
    },
  },
  {
    name: 'change_deal_status',
    title: 'Change deal status',
    icon: markRaw(StepsIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#activity',
        })
      } else {
        router.push({ name: 'Leads' })
      }
    },
  },
])

async function getFirstLead() {
  if (firstLead.value) return firstLead.value
  return await call('crm.api.onboarding.get_first_lead')
}

async function getFirstDeal() {
  if (firstDeal.value) return firstDeal.value
  return await call('crm.api.onboarding.get_first_deal')
}

const stepsCompleted = computed(
  () => steps.filter((step) => step.completed).length,
)
const totalSteps = ref(steps.length)

const completedPercentage = computed(() =>
  Math.floor((stepsCompleted.value / totalSteps.value) * 100),
)

export function useOnboarding() {
  router = useRouter()

  syncStatus()

  function skip(step) {
    updateOnboardingStep(step, true)
  }

  function skipAll() {
    updateAll(true)
  }

  function reset() {
    updateAll(false)
  }

  function updateOnboardingStep(step, skipped = false) {
    if (isOnboardingStepsCompleted.value) return
    let user = window.user
    if (!user) return false

    if (!user.onboarding_status['frappe_crm_onboarding_status']) {
      user.onboarding_status['frappe_crm_onboarding_status'] = steps.map(
        (s) => {
          return { name: s.name, completed: false }
        },
      )
    }

    let _steps = user.onboarding_status['frappe_crm_onboarding_status']
    let index = _steps.findIndex((s) => s.name === step)
    if (index !== -1) {
      _steps[index].completed = true
      steps[index].completed = true
    }

    window.user = user

    if (skipped) {
      capture('onboarding_skipped_' + step)
    } else {
      capture('onboarding_' + step)
    }

    call('crm.api.onboarding.update_user_onboarding_status', {
      steps: JSON.stringify(_steps),
    })
  }

  function updateAll(value) {
    if (isOnboardingStepsCompleted.value) return
    let user = window.user
    if (!user) return false

    let _steps

    if (!user.onboarding_status['frappe_crm_onboarding_status']) {
      user.onboarding_status['frappe_crm_onboarding_status'] = steps.map(
        (s) => {
          return { name: s.name, completed: value }
        },
      )
    } else {
      _steps = user.onboarding_status['frappe_crm_onboarding_status']
      _steps.forEach((step) => {
        step.completed = value
      })
    }

    steps.forEach((step) => {
      step.completed = value
    })

    window.user = user

    capture(value ? 'onboarding_skipped_all' : 'onboarding_reset_steps')

    call('crm.api.onboarding.update_user_onboarding_status', {
      steps: JSON.stringify(_steps),
    })
  }

  function syncStatus() {
    if (isOnboardingStepsCompleted.value) return
    let user = window.user
    if (!user) return false

    if (user.onboarding_status['frappe_crm_onboarding_status']) {
      let _steps = user.onboarding_status['frappe_crm_onboarding_status']
      _steps.forEach((step, index) => {
        steps[index].completed = step.completed
      })
      isOnboardingStepsCompleted.value = _steps.every((step) => step.completed)
    } else {
      isOnboardingStepsCompleted.value = false
    }
  }

  return {
    steps,
    stepsCompleted,
    totalSteps,
    completedPercentage,
    updateOnboardingStep,
    skip,
    skipAll,
    reset,
  }
}
