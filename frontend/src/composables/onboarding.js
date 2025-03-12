import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import ConvertIcon from '@/components/Icons/ConvertIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import { ref, reactive, computed, markRaw } from 'vue'

const steps = reactive([
  {
    title: 'Create your first lead',
    icon: markRaw(LeadsIcon),
    completed: true,
  },
  {
    title: 'Invite your team',
    icon: markRaw(InviteIcon),
    completed: false,
  },
  {
    title: 'Convert lead to deal',
    icon: markRaw(ConvertIcon),
    completed: false,
  },
  {
    title: 'Create your first note',
    icon: markRaw(NoteIcon),
    completed: false,
  },
  {
    title: 'Create your first task',
    icon: markRaw(TaskIcon),
    completed: false,
  },
  {
    title: 'Add your first comment',
    icon: markRaw(CommentIcon),
    completed: false,
  },
  {
    title: 'Send email',
    icon: markRaw(EmailIcon),
    completed: false,
  },
  {
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
  const incrementStep = () => {
    stepsCompleted.value++
  }

  const decrementStep = () => {
    stepsCompleted.value--
  }

  return {
    steps,
    stepsCompleted,
    totalSteps,
    completedPercentage,
    incrementStep,
    decrementStep,
  }
}
