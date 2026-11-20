<template>
  <aside
    ref="stage"
    class="overflow-hidden border-l border-outline-gray-2 bg-surface-gray-1"
    aria-hidden="true"
    inert
  >
    <div
      class="absolute top-0 flex h-[72px] items-center"
      :style="{ left: box.left + 'px' }"
    >
      <span class="text-base text-ink-gray-6">
        {{ __('What your team sees') }}
      </span>
    </div>

    <div
      class="absolute"
      :style="{
        left: box.left + 'px',
        top: box.top + 'px',
        width: box.width + 'px',
        height: box.height + 'px',
      }"
    >
      <div
        class="origin-top-left"
        :style="{
          width: W + 'px',
          height: H + 'px',
          transform: `scale(${scale})`,
        }"
      >
        <div
          class="absolute inset-x-12 -top-7 h-full rounded-[16px] border border-outline-gray-2 bg-surface-gray-2 opacity-60"
        />
        <div
          class="absolute inset-x-6 -top-3.5 h-full rounded-[16px] border border-outline-gray-2 bg-surface-gray-2"
        />

        <div
          class="absolute inset-0 flex flex-col overflow-hidden rounded-[16px] border border-outline-gray-2 bg-surface-base"
        >
          <div
            class="relative flex h-11 shrink-0 items-end gap-1 bg-surface-gray-2 px-3"
          >
            <div class="flex h-full items-center gap-2 pe-4 ps-1">
              <span
                v-for="light in TRAFFIC_LIGHTS"
                :key="light"
                class="size-3 rounded-full border border-black/10"
                :class="light"
              />
            </div>
            <div
              class="flex h-9 w-[240px] items-center gap-2 rounded-t-[10px] bg-surface-base px-3"
            >
              <CRMLogo class="size-4 shrink-0 rounded-[4px]" />
              <Transition v-bind="fade">
                <span
                  :key="title"
                  class="min-w-0 flex-1 truncate text-sm text-ink-gray-8"
                >
                  {{ title }}
                </span>
              </Transition>
              <span class="lucide-x size-3.5 text-ink-gray-5" />
            </div>
            <span
              class="lucide-plus mb-2.5 ms-1 size-4 self-end text-ink-gray-6"
            />
          </div>
          <div
            class="flex h-11 shrink-0 items-center gap-4 border-b border-outline-gray-1 px-4"
          >
            <span class="lucide-arrow-left size-4 text-ink-gray-4" />
            <span class="lucide-arrow-right size-4 text-ink-gray-4" />
            <span class="lucide-rotate-cw size-4 text-ink-gray-4" />
            <div
              class="flex h-7 flex-1 items-center gap-2 rounded-full bg-surface-gray-2 px-3"
            >
              <span class="lucide-lock size-3.5 text-ink-gray-5" />
              <Transition v-bind="fade">
                <span :key="url" class="text-sm text-ink-gray-7">
                  {{ url }}
                </span>
              </Transition>
              <span class="lucide-star ms-auto size-3.5 text-ink-gray-5" />
            </div>
            <Avatar
              :label="user.full_name"
              :image="user.user_image"
              size="sm"
            />
            <span class="lucide-ellipsis-vertical size-4 text-ink-gray-5" />
          </div>

          <div class="relative min-h-0 flex-1 overflow-hidden">
            <Transition v-bind="slide">
              <SetupPreviewLogin v-if="page === 'login'" key="login" :state />
              <SetupPreviewApp v-else key="app" :page :state />
            </Transition>
          </div>
        </div>

        <div
          v-if="!reducedMotion"
          class="pointer-events-none absolute left-0 top-0 z-10 transition-transform duration-700 ease-[cubic-bezier(.65,0,.35,1)]"
          :style="{ transform: `translate(${cursor.x}px, ${cursor.y}px)` }"
        >
          <span
            ref="ripple"
            class="absolute -left-4 -top-4 size-8 rounded-full bg-surface-gray-9 opacity-0"
          />
          <div ref="cursorEl" class="origin-top-left">
            <svg class="size-5 drop-shadow-md" viewBox="0 0 20 20" fill="none">
              <path
                d="M3 2 L3 16 L7 12.5 L9.6 18 L12 17 L9.5 11.6 L15 11.4 Z"
                fill="#111"
                stroke="#fff"
                stroke-width="1.4"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreviewApp from '@/components/Setup/SetupPreviewApp.vue'
import SetupPreviewLogin from '@/components/Setup/SetupPreviewLogin.vue'
import { SAMPLE_LEAD } from '@/components/Setup/setupPreviewData'
import { usersStore } from '@/stores/users'
import { useElementSize, usePreferredReducedMotion } from '@vueuse/core'
import { Avatar } from 'frappe-ui'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'

const props = defineProps({
  step: { type: String, required: true },
  state: { type: Object, required: true },
})

const TRAFFIC_LIGHTS = ['bg-[#ff5f57]', 'bg-[#febc2e]', 'bg-[#28c840]']
const W = 1120
const H = 720
const SITE = window.location.host

const { getUser } = usersStore()
const user = computed(() => getUser() || {})

const stage = ref(null)
const { width, height } = useElementSize(stage)
const scale = computed(
  () => Math.min(1.15, (width.value * 0.92) / 0.75 / W) || 0.9,
)
const box = computed(() => ({
  left: width.value * 0.08,
  top: Math.max(84, height.value * 0.14),
  width: W * scale.value,
  height: H * scale.value,
}))

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

const REST = {
  login: { x: 560, y: 470 },
  lead: { x: 620, y: 420 },
  leads: { x: 460, y: 440 },
}
const CLICKS = {
  'lead>leads': { x: 72, y: 312 },
  'leads>lead': { x: 200, y: 200 },
}

const cursor = reactive({ ...REST[page.value] })
const cursorEl = ref(null)
const ripple = ref(null)

function click() {
  cursorEl.value?.animate(
    [
      { transform: 'scale(1)' },
      { transform: 'scale(.82)' },
      { transform: 'scale(1)' },
    ],
    { duration: 260, easing: 'ease-out' },
  )
  ripple.value?.animate(
    [
      { transform: 'scale(.3)', opacity: 0.5 },
      { transform: 'scale(1.8)', opacity: 0 },
    ],
    { duration: 600, easing: 'ease-out' },
  )
}

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
    Object.assign(cursor, REST[to])
    return
  }
  Object.assign(cursor, point)
  later(800, () => {
    click()
    page.value = to
    later(650, () => Object.assign(cursor, REST[to]))
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
const fade = {
  mode: 'out-in',
  enterActiveClass:
    'transition duration-300 ease-out motion-reduce:transition-none',
  enterFromClass: 'opacity-0',
  leaveActiveClass: 'transition duration-150 motion-reduce:transition-none',
  leaveToClass: 'opacity-0',
}
</script>
