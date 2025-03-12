import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import { useRouter } from 'vue-router'
import { ref, reactive, computed, markRaw } from 'vue'

let router

const minimize = ref(false)

const steps = reactive([
  {
    name: 'create_first_lead',
    title: 'Create your first lead',
    icon: markRaw(LeadsIcon),
    completed: false,
    onClick: () => {
      if (steps[0].completed) return
      minimize.value = true

      router.push({ name: 'Leads' })
    },
  },
  {
    name: 'invite_your_team',
    title: 'Invite your team',
    icon: markRaw(InviteIcon),
    completed: false,
  },
  {
    name: 'convert_lead_to_deal',
    title: 'Convert lead to deal',
    icon: markRaw(ConvertIcon),
    completed: false,
  },
  {
    name: 'create_first_note',
    title: 'Create your first note',
    icon: markRaw(NoteIcon),
    completed: false,
  },
  {
    name: 'create_first_task',
    title: 'Create your first task',
    icon: markRaw(TaskIcon),
    completed: false,
  },
  {
    name: 'add_first_comment',
    title: 'Add your first comment',
    icon: markRaw(CommentIcon),
    completed: false,
  },
  {
    name: 'send_email',
    title: 'Send email',
    icon: markRaw(EmailIcon),
    completed: false,
  },
  {
    name: 'change_deal_status',
    title: 'Change deal status',
    icon: markRaw(StepsIcon),
    completed: false,
  },
])

const stepsCompleted = computed(
  () => steps.filter((step) => step.completed).length,
)
const totalSteps = ref(steps.length)

const completedPercentage = computed(() =>
  Math.floor((stepsCompleted.value / totalSteps.value) * 100),
)

export function useOnboarding() {
  router = useRouter()

  function checkOnboardingStatus() {
    let user = window.user
    if (!user) return false
    if (user.onboarding_status['frappe_crm_onboarding_status']) {
      return user.onboarding_status['frappe_crm_onboarding_status'].every(
        (step) => step.completed,
      )
    }
    return false
  }

  return {
    minimize,
    steps,
    stepsCompleted,
    totalSteps,
    completedPercentage,
    checkOnboardingStatus,
  }
}
