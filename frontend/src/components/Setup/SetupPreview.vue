<template>
  <SetupPreviewFrame
    ref="frame"
    :url="url"
    :tabs="[{ title, active: true }]"
    :user="{ name: user.full_name, image: user.user_image }"
    :cursor="cursor"
  >
    <template #tab-icon>
      <CRMLogo class="size-full" />
    </template>
    <Transition v-bind="slide">
      <SetupPreviewLogin v-if="page === 'login'" key="login" :state />
      <SetupPreviewApp v-else key="app" :page :state />
    </Transition>
  </SetupPreviewFrame>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreviewApp from '@/components/Setup/SetupPreviewApp.vue'
import SetupPreviewLogin from '@/components/Setup/SetupPreviewLogin.vue'
import { SAMPLE_LEAD } from '@/components/Setup/setupPreviewData'
import { usersStore } from '@/stores/users'
import { SetupPreviewFrame } from '@framework/ui/components/SetupFlow'
import { usePreferredReducedMotion } from '@vueuse/core'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  step: { type: String, required: true },
  state: { type: Object, required: true },
})

const SITE = window.location.host

const { getUser } = usersStore()
const user = computed(() => getUser() || {})

const PAGES = {
  set_password: 'login',
  connect_email: 'lead',
  bring_leads: 'leads',
  invite_team: 'leads',
}
const target = computed(() => PAGES[props.step] || 'lead')

const motion = usePreferredReducedMotion()
const reducedMotion = computed(() => motion.value === 'reduce')
const page = ref(target.value)

// Where the pointer rests on each page, and where it clicks to go from one to the next,
// in the app's pixels below the browser bar.
const REST = {
  login: '[data-slot="setup-preview-login-submit"]',
  lead: { x: 620, y: 332 },
  leads: { x: 460, y: 352 },
}
const CLICKS = {
  'lead>leads': { x: 72, y: 224 },
  'leads>lead': { x: 200, y: 112 },
}

const frame = ref(null)
const cursor = ref(REST[page.value])

let timers = []
const later = (ms, fn) => timers.push(window.setTimeout(fn, ms))
const clearTimers = () => {
  timers.forEach(clearTimeout)
  timers = []
}

watch(target, (to) => {
  clearTimers()
  const point = CLICKS[`${page.value}>${to}`]
  if (reducedMotion.value || !point) {
    page.value = to
    cursor.value = REST[to]
    return
  }
  cursor.value = point
  later(800, () => {
    frame.value?.click()
    page.value = to
    later(650, () => (cursor.value = REST[to]))
  })
})
onBeforeUnmount(clearTimers)

const PATHS = {
  login: '/login',
  lead: `/crm/leads/${SAMPLE_LEAD.id}`,
  leads: '/crm/leads/view/list',
}
const url = computed(() => SITE + PATHS[page.value])
const title = computed(
  () =>
    ({
      login: __('Login'),
      lead: SAMPLE_LEAD.name,
      leads: __('Leads'),
    })[page.value],
)

const slide = {
  enterActiveClass:
    'transition duration-500 delay-100 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none',
  enterFromClass: 'opacity-0 translate-x-8',
  leaveActiveClass:
    'absolute inset-0 transition duration-150 ease-in motion-reduce:transition-none',
  leaveToClass: 'opacity-0',
}
</script>
