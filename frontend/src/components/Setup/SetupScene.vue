<template>
  <div
    class="scene relative flex items-center justify-center overflow-hidden"
    :class="fx.map((f) => `fx-${f}`)"
    :style="{ ...pointer, '--click': `${clickAt}ms` }"
    @mousemove="onMove"
  >
    <div class="glow pointer-events-none absolute inset-0" />
    <div
      class="camera relative -ml-[116px] -mt-[152px] h-[640px] w-[540px] shrink-0"
    >
      <div class="window absolute left-12 top-24 h-[600px] w-[560px]">
        <div class="hair relative flex h-11 items-center gap-3 border-b px-4">
          <div class="flex gap-1.5">
            <span v-for="i in 3" :key="i" class="light size-2.5 rounded-full" />
          </div>
          <div
            class="url mx-auto flex h-6 w-60 items-center justify-center gap-1.5 rounded-full text-xs text-ink-gray-5"
          >
            <LockIcon class="size-3" />acme.frappe.cloud
          </div>
          <Sk w="14px" /><Sk w="14px" />
          <span class="loadbar absolute -bottom-px left-0 h-0.5" />
        </div>
        <div
          class="hair flex flex-col items-center gap-2 border-b px-4 pb-2.5 pt-2"
        >
          <span class="inline-flex items-center gap-1 text-xs font-medium text-ink-gray-5">
            Acme
            <ChevronDownIcon class="size-3 shrink-0 text-ink-gray-4" aria-hidden="true" />
          </span>
          <div class="flex w-full items-center gap-3 pl-24">
            <span class="hair-strong h-4 w-20 rounded-4 border" />
            <Sk v-for="i in 3" :key="i" w="10px" />
            <span class="h-3 w-px" style="background: var(--st-hair-strong)" />
            <Sk v-for="i in 3" :key="'b' + i" w="12px" />
          </div>
        </div>
        <div class="spot pointer-events-none absolute inset-0" />
        <div class="sheen pointer-events-none absolute inset-0" />
      </div>

      <div :key="step + run" class="absolute inset-0">
        <div
          class="frag blank back absolute left-3 top-[250px] h-36 w-28"
          style="--r: -6deg; --d: 150ms"
        />
        <div
          class="frag back absolute left-12 top-[340px] flex h-32 w-28 flex-col items-center justify-center gap-1 text-sm text-ink-gray-5"
          style="--r: 4deg; --d: 250ms"
        >
          <span class="text-lg leading-none text-ink-gray-4">+</span
          >{{ ADD[step] }}
        </div>

        <template v-if="step === 'email'">
          <div
            class="frag absolute left-[190px] top-[200px] w-[250px] p-4"
            style="--r: 3deg; --d: 320ms"
          >
            <div class="flex items-center gap-2">
              <Sk circle :size="22" /><span
                class="text-sm font-medium text-ink-gray-6"
                >Marcus Lee</span
              >
            </div>
            <div class="mt-3 text-sm font-medium text-ink-gray-7">
              Re: Pricing for 40 seats
            </div>
            <div class="mt-2.5 flex flex-col gap-2">
              <Sk w="92%" /><Sk w="80%" /><Sk w="55%" />
            </div>
            <div class="mt-4 h-4 text-xs text-ink-gray-5">
              to <span class="text-ink-gray-8">{{ typed }}</span
              ><span class="caret" />
            </div>
          </div>
          <div
            class="frag absolute left-[320px] top-[372px] w-[230px] p-2"
            style="--r: -3deg; --d: 460ms"
          >
            <div class="px-2 pb-2 pt-1 text-xs text-ink-gray-5">
              Email provider
            </div>
            <div class="relative">
              <span class="hl absolute inset-x-0 top-0 h-8 rounded-5" />
              <div
                v-for="p in PROVIDERS"
                :key="p"
                class="relative flex h-8 items-center gap-2 px-2 text-sm"
                :class="
                  p === 'Gmail' ? 'pick text-ink-gray-8' : 'text-ink-gray-5'
                "
              >
                <span class="radio size-3.5 rounded-full border" />{{ p }}
              </div>
            </div>
          </div>
          <div class="cursor-wrap path-email absolute left-[420px] top-[414px]">
            <span class="ripple absolute -left-3 -top-3 size-6 rounded-full" />
            <Cursor class="cursor" />
          </div>
        </template>

        <template v-else-if="step === 'leads'">
          <div
            class="frag absolute left-[180px] top-[190px] w-[270px] py-3"
            style="--r: 2deg; --d: 320ms"
          >
            <div class="flex items-baseline justify-between px-4 pb-2">
              <span class="text-sm font-medium text-ink-gray-7">Leads</span>
              <span class="text-xs tabular-nums text-ink-gray-5">{{
                count
              }}</span>
            </div>
            <div
              v-for="(l, i) in rows"
              :key="i"
              class="hair flex items-center gap-2.5 border-t px-4 py-2.5"
            >
              <Sk circle :size="18" />
              <span v-if="l" class="row-in flex-1 text-sm text-ink-gray-7">{{
                l.name
              }}</span>
              <Sk v-else w="40%" />
              <Sk v-if="l" w="36px" />
            </div>
          </div>
          <div
            class="frag absolute left-[330px] top-[400px] w-[220px] p-3.5"
            style="--r: -4deg; --d: 460ms"
          >
            <div class="text-sm font-medium text-ink-gray-7">{{ FILE }}</div>
            <div
              class="mt-3 h-1.5 overflow-hidden rounded-full"
              style="background: var(--st-skel)"
            >
              <div class="fill h-full rounded-full bg-ink-gray-6" />
            </div>
            <div class="mt-2 text-xs tabular-nums text-ink-gray-5">
              {{ count }} of 48 imported
            </div>
          </div>
          <div
            class="dragfile frag absolute left-[436px] top-[452px] items-center gap-1.5 px-2.5 py-1.5 text-xs text-ink-gray-7"
            style="--r: -8deg"
          >
            <FileIcon class="size-3.5" />{{ FILE }}
          </div>
          <div class="cursor-wrap absolute left-[470px] top-[440px]">
            <span class="ripple absolute -left-3 -top-3 size-6 rounded-full" />
            <Cursor class="cursor" />
          </div>
        </template>

        <template v-else>
          <div
            class="frag absolute left-[180px] top-[190px] w-[260px] py-3"
            style="--r: 2deg; --d: 320ms"
          >
            <div class="px-4 pb-2 text-sm font-medium text-ink-gray-7">
              Members
            </div>
            <div
              v-for="(m, i) in members"
              :key="i"
              class="hair flex items-center gap-2.5 border-t px-4 py-2.5"
            >
              <Sk circle :size="18" />
              <span v-if="m" class="row-in flex-1 text-sm text-ink-gray-7">{{
                m.name
              }}</span>
              <Sk v-else w="45%" />
              <span v-if="m" class="text-xs text-ink-gray-5">{{ m.role }}</span>
            </div>
          </div>
          <div
            class="frag absolute left-[300px] top-[390px] w-[250px] p-3"
            style="--r: -3deg; --d: 460ms"
          >
            <div
              class="field h-8 rounded-5 border px-2.5 py-1.5 text-sm text-ink-gray-8"
            >
              {{ typed }}<span class="caret" />
            </div>
            <div class="mt-2 flex items-center gap-2">
              <span
                class="hair-strong inline-flex items-center gap-1 rounded-5 border px-2.5 py-1 text-sm text-ink-gray-6"
                >{{ role }}<ChevronDownIcon class="size-3.5 shrink-0" aria-hidden="true" /></span
              >
              <span
                class="press ml-auto rounded-5 px-2.5 py-1 text-sm font-medium text-ink-gray-8"
                >Send invites</span
              >
            </div>
          </div>
          <div
            class="menu frag absolute left-[300px] top-[468px] w-36 p-1"
            style="--r: -3deg"
          >
            <div
              v-for="r in ['Sales User', 'Manager', 'Admin']"
              :key="r"
              class="flex h-7 items-center rounded-4 px-2 text-sm"
              :class="
                r === 'Manager'
                  ? 'menu-pick text-ink-gray-8'
                  : 'text-ink-gray-5'
              "
            >
              {{ r }}
            </div>
          </div>
          <div class="cursor-wrap path-team absolute left-[500px] top-[450px]">
            <span class="ripple absolute -left-3 -top-3 size-6 rounded-full" />
            <Cursor class="cursor" />
          </div>
        </template>

        <div
          class="toast frag absolute bottom-8 right-8 items-center gap-2 px-3 py-2 text-sm text-ink-gray-8"
          style="--r: 0deg"
        >
          <CheckIcon class="size-4 text-ink-gray-6" />{{ TOAST[step] }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LockIcon from '~icons/lucide/lock'
import ChevronDownIcon from '~icons/lucide/chevron-down'
import CheckIcon from '~icons/lucide/circle-check'
import FileIcon from '~icons/lucide/file-spreadsheet'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import Sk from '@/components/Setup/SetupSceneSkeleton.vue'
import Cursor from '@/components/Setup/SetupSceneCursor.vue'

const props = defineProps({
  step: { type: String, required: true },
  fx: { type: Array, default: () => [] },
  run: { type: Number, default: 0 },
})

const EMAIL = 'alex@acme.com'
const FILE = 'acme-leads.csv'
const LEADS = [
  { name: 'Priya Raman' },
  { name: 'Marcus Lee' },
  { name: 'Ana Souza' },
]
const TEAM = [
  { name: 'Alex Rivera', role: 'Admin' },
  { name: 'Ria Kapoor', role: 'Manager' },
  { name: 'Joe Mills', role: 'Sales User' },
]
const ADD = { email: 'New email', leads: 'Import', team: 'Invite' }
const TOAST = {
  email: 'Gmail connected',
  leads: '21 leads imported',
  team: 'Invite sent to Ria',
}
const PROVIDERS = ['Gmail', 'Outlook', 'Frappe Mail', 'Yahoo']
const INVITE = 'ria.kapoor@acme.com'

const journey = computed(() => props.fx.includes('journey'))
const clickAt = computed(() => {
  if (props.step === 'email') return journey.value ? 2800 : 1750
  if (props.step === 'team') return journey.value ? 3350 : 2250
  return 1750
})

const typed = ref('')
const count = ref(0)
const added = ref(false)
const role = ref('Manager')
let timers = []

function later(fn, ms) {
  timers.push(setTimeout(fn, ms))
}

function typeOut(text, start) {
  typed.value = ''
  ;[...text].forEach((_, i) =>
    later(() => (typed.value = text.slice(0, i + 1)), start + i * 45),
  )
}

function countTo(target, start, duration) {
  count.value = 0
  for (let i = 1; i <= 20; i++)
    later(
      () => (count.value = Math.round((target * i) / 20)),
      start + (duration * i) / 20,
    )
}

function play() {
  timers.forEach(clearTimeout)
  timers = []
  added.value = false
  role.value = journey.value ? 'Sales User' : 'Manager'
  const click = clickAt.value
  if (props.step === 'email') typeOut(EMAIL, click + 150)
  if (props.step === 'leads') countTo(21, click, 1500)
  if (props.step === 'team') {
    typeOut(INVITE, 900)
    if (journey.value) later(() => (role.value = 'Manager'), 2650)
    later(() => (added.value = true), click + 100)
  }
}

watch(() => [props.step, props.run], play, { immediate: true })
onBeforeUnmount(() => timers.forEach(clearTimeout))

const rows = computed(() => {
  const real = LEADS.slice(0, 3).filter((_, i) => count.value > i * 6)
  return [...real, ...Array(6 - real.length).fill(null)]
})

const members = computed(() => {
  const list = added.value ? TEAM : [TEAM[0], TEAM[2]]
  return [...list, ...Array(5 - list.length).fill(null)]
})

const pointer = ref({})
function onMove(event) {
  const box = event.currentTarget.getBoundingClientRect()
  pointer.value = {
    '--sx': `${event.clientX - box.left - 48}px`,
    '--sy': `${event.clientY - box.top - 96}px`,
  }
  const card = event.target.closest('.frag')
  if (!card) return
  const bounds = card.getBoundingClientRect()
  card.style.setProperty('--hover-x', `${((event.clientX - bounds.left) / bounds.width) * 100}%`)
  card.style.setProperty('--hover-y', `${((event.clientY - bounds.top) / bounds.height) * 100}%`)
}
</script>

<style scoped>
.scene {
  --st-bg: var(--surface-base);
  --st-win: linear-gradient(
    to bottom,
    var(--surface-base),
    var(--surface-gray-1) 140px
  );
  --st-hair: var(--outline-gray-2);
  --st-hair-strong: var(--outline-gray-3);
  --st-frag: var(--surface-gray-1);
  --st-blank: var(--surface-base);
  --st-skel: color-mix(in srgb, var(--surface-gray-3) 65%, var(--surface-gray-4));
  --st-skel-hi: var(--surface-gray-2);
  --st-halo: color-mix(in oklch, var(--surface-gray-2) 70%, transparent);
  --st-hi: rgb(255 255 255 / 0.7);
  --st-pick: var(--surface-gray-3);
  --st-sheen: rgb(255 255 255 / 0.6);
  --st-glow: transparent;
  --st-frag-shadow: 0 1px 2px rgb(0 0 0 / 0.04),
    0 10px 24px -14px rgb(0 0 0 / 0.18);
  --st-win-shadow: 0 40px 80px -40px rgb(0 0 0 / 0.35);
  --sx: 50%;
  --sy: 40%;
  background: var(--st-bg);
}

/* Dark: translucent white hairlines and highlights so layers separate */
:root[data-theme='dark'] .scene {
  --st-bg: color-mix(in oklch, var(--surface-base) 55%, black);
  --st-win: linear-gradient(
      to bottom,
      rgb(255 255 255 / 0.045),
      rgb(255 255 255 / 0.015) 180px
    ),
    var(--surface-base);
  --st-hair: rgb(255 255 255 / 0.07);
  --st-hair-strong: rgb(255 255 255 / 0.11);
  --st-frag: color-mix(in oklch, var(--surface-base) 90%, white);
  --st-blank: color-mix(in oklch, var(--surface-base) 94%, white);
  --st-skel: rgb(255 255 255 / 0.1);
  --st-skel-hi: rgb(255 255 255 / 0.18);
  --st-halo: rgb(255 255 255 / 0.03);
  --st-hi: rgb(255 255 255 / 0.06);
  --st-pick: rgb(255 255 255 / 0.08);
  --st-sheen: rgb(255 255 255 / 0.07);
  --st-glow: rgb(255 255 255 / 0.05);
  --st-frag-shadow: 0 18px 36px -14px rgb(0 0 0 / 0.7),
    0 2px 6px rgb(0 0 0 / 0.3);
  --st-win-shadow: 0 50px 100px -30px rgb(0 0 0 / 0.8);
}

.hair {
  border-color: var(--st-hair);
}
.hair-strong {
  border-color: var(--st-hair-strong);
}

.glow {
  background: radial-gradient(60% 40% at 50% 20%, var(--st-glow), transparent);
}

.window {
  border-radius: 18px;
  border: 1px solid var(--st-hair-strong);
  background: var(--st-win);
  overflow: hidden;
  box-shadow:
    inset 0 1px 0 var(--st-hi),
    0 0 0 6px var(--st-halo),
    0 0 0 7px var(--st-hair),
    var(--st-win-shadow);
  animation: rise 700ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.light {
  background: var(--st-skel);
}
.url {
  background: var(--st-skel);
  box-shadow: inset 0 0 0 1px var(--st-hair);
}
.loadbar,
.spot,
.sheen,
.dragfile,
.menu,
.toast,
.ripple,
.hl {
  display: none;
}

.frag {
  border-radius: 12px;
  border: 1px solid var(--st-hair-strong);
  background: var(--st-frag);
  box-shadow:
    inset 0 1px 0 var(--st-hi),
    var(--st-frag-shadow);
  transform: rotate(var(--r));
  animation: drop 800ms cubic-bezier(0.2, 0.9, 0.3, 1.15) var(--d) both;
}
.blank {
  background: var(--st-blank);
}

@media (hover: hover) and (pointer: fine) {
  .frag:not(.toast):not(.dragfile):not(.menu) {
    transition: translate 180ms ease, scale 180ms ease, box-shadow 180ms ease,
      border-color 180ms ease;
  }
  .frag:not(.toast):not(.dragfile):not(.menu)::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    background: radial-gradient(
      160px circle at var(--hover-x, 50%) var(--hover-y, 50%),
      color-mix(in srgb, var(--surface-gray-4) 22%, transparent),
      transparent 75%
    );
    opacity: 0;
    transition: opacity 180ms ease;
  }
  .frag:not(.toast):not(.dragfile):not(.menu):hover {
    translate: 0 -4px;
    scale: 1.015;
    border-color: var(--outline-gray-4);
    box-shadow: inset 0 1px 0 var(--st-hi), var(--elevation-md);
  }
  .frag:hover::after {
    opacity: 1;
  }
}
.field {
  border-color: var(--st-hair-strong);
  background: var(--st-bg);
}
.radio {
  border-color: var(--st-hair-strong);
}
.press {
  background: var(--st-pick);
  animation: press 220ms ease var(--click);
}

.cursor-wrap {
  animation: cursor-in 900ms cubic-bezier(0.3, 0.7, 0.2, 1) 800ms both;
}
.cursor {
  animation: click 220ms ease var(--click);
}
.pick {
  border-radius: 5px;
  animation: pick 200ms ease calc(var(--click) + 50ms) both;
}
.pick .radio {
  animation: radio 200ms ease calc(var(--click) + 50ms) both;
}
.fill {
  width: 44%;
  animation: fill 1500ms cubic-bezier(0.4, 0, 0.2, 1) var(--click) both;
}
.row-in {
  animation: fade 300ms ease both;
}
.caret {
  display: inline-block;
  width: 1px;
  height: 0.9em;
  margin-left: 1px;
  vertical-align: -0.1em;
  background: var(--ink-gray-6);
  animation: blink 1s steps(1) infinite;
}

/* fx: click ripple */
.fx-ripple .ripple {
  display: block;
  border: 1.5px solid var(--ink-gray-5);
  animation: ripple 650ms ease-out var(--click) both;
}

/* fx: browser load bar */
.fx-loadbar .loadbar {
  display: block;
  background: var(--ink-gray-5);
  animation: load 1100ms cubic-bezier(0.4, 0, 0.2, 1) 200ms both;
}

/* fx: completion toast */
.fx-toast .toast {
  display: flex;
  animation: toast 500ms cubic-bezier(0.2, 0.9, 0.3, 1.15)
    calc(var(--click) + 1700ms) both;
}

/* fx: skeleton shimmer */
.fx-shimmer :deep(.sk:not(.outline)) {
  background: linear-gradient(
    90deg,
    var(--st-skel) 0%,
    var(--st-skel-hi) 50%,
    var(--st-skel) 100%
  );
  background-size: 300% 100%;
  animation: shimmer 2.2s linear infinite;
}

/* fx: one sheen pass across the window */
.fx-sheen .sheen {
  display: block;
  background: linear-gradient(
    105deg,
    transparent 35%,
    var(--st-sheen) 50%,
    transparent 65%
  );
  background-size: 300% 100%;
  animation: sheen 1600ms ease-in-out 500ms both;
}

/* fx: pointer spotlight */
.fx-spotlight .spot {
  display: block;
  background: radial-gradient(
    220px circle at var(--sx) var(--sy),
    var(--st-sheen),
    transparent 70%
  );
}

/* fx: ambient bob */
.fx-bob .frag:not(.toast):not(.dragfile):not(.menu) {
  animation:
    drop 800ms cubic-bezier(0.2, 0.9, 0.3, 1.15) var(--d) both,
    bob 7s ease-in-out calc(var(--d) + 900ms) infinite;
}

/* fx: slow camera push toward the live fragments, soft focus on back cards */
.fx-camera .camera {
  transform-origin: 70% 65%;
  animation: camera 9s cubic-bezier(0.4, 0, 0.2, 1) 400ms both;
}
.fx-camera .back {
  filter: blur(0.8px);
  opacity: 0.85;
}

/* fx: guided journey, the cursor explores before choosing */
.fx-journey .hl {
  display: block;
  background: var(--st-pick);
  animation: hl-journey 2000ms ease-in-out 800ms both;
}
.fx-journey .pick {
  animation: none;
  background: none;
}
.fx-journey .path-email {
  animation: path-email 2000ms ease-in-out 800ms both;
}
.fx-journey .path-team {
  animation: path-team 2550ms ease-in-out 800ms both;
}
.fx-journey .dragfile {
  display: flex;
  animation:
    cursor-in 900ms cubic-bezier(0.3, 0.7, 0.2, 1) 800ms both,
    absorb 300ms ease var(--click) forwards;
}
.fx-journey .menu {
  display: block;
  transform-origin: top left;
  animation: menu 1000ms ease 2150ms both;
}
.fx-journey .menu-pick {
  animation: pick 150ms ease 2550ms both;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(28px);
  }
}
@keyframes drop {
  from {
    opacity: 0;
    transform: translateY(26px) rotate(calc(var(--r) - 7deg)) scale(0.95);
  }
}
@keyframes bob {
  50% {
    transform: rotate(calc(var(--r) * 0.6)) translateY(-6px);
  }
}
@keyframes cursor-in {
  from {
    opacity: 0;
    transform: translate(90px, 150px);
  }
}
@keyframes click {
  50% {
    transform: scale(0.82);
  }
}
@keyframes ripple {
  0% {
    opacity: 0;
    transform: scale(0.2);
  }
  5% {
    opacity: 0.7;
  }
  100% {
    opacity: 0;
    transform: scale(2.6);
  }
}
@keyframes load {
  0% {
    width: 0;
    opacity: 1;
  }
  80% {
    width: 100%;
    opacity: 1;
  }
  100% {
    width: 100%;
    opacity: 0;
  }
}
@keyframes toast {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.96);
  }
}
@keyframes shimmer {
  from {
    background-position: 100% 0;
  }
  to {
    background-position: -50% 0;
  }
}
@keyframes sheen {
  from {
    background-position: 120% 0;
  }
  to {
    background-position: -40% 0;
  }
}
@keyframes camera {
  to {
    transform: scale(1.07) translate(-10px, -6px);
  }
}
@keyframes pick {
  from {
    background: transparent;
  }
  to {
    background: var(--st-pick);
  }
}
@keyframes radio {
  to {
    border-width: 4px;
    border-color: var(--ink-gray-7);
  }
}
@keyframes press {
  50% {
    transform: scale(0.94);
  }
}
@keyframes fill {
  from {
    width: 0;
  }
}
@keyframes fade {
  from {
    opacity: 0;
    transform: translateY(3px);
  }
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
@keyframes absorb {
  to {
    opacity: 0;
    transform: rotate(var(--r)) scale(0.6) translate(-10px, -30px);
  }
}
@keyframes menu {
  0% {
    opacity: 0;
    transform: rotate(var(--r)) scale(0.92);
  }
  15%,
  75% {
    opacity: 1;
    transform: rotate(var(--r)) scale(1);
  }
  100% {
    opacity: 0;
    transform: rotate(var(--r)) scale(0.96);
  }
}
@keyframes hl-journey {
  0%,
  24% {
    opacity: 0;
    transform: translateY(32px);
  }
  25%,
  35% {
    opacity: 1;
    transform: translateY(32px);
  }
  50%,
  58% {
    transform: translateY(64px);
  }
  75%,
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
@keyframes path-email {
  0% {
    opacity: 0;
    transform: translate(90px, 150px);
  }
  25%,
  35% {
    opacity: 1;
    transform: translate(0, 32px);
  }
  50%,
  58% {
    transform: translate(6px, 64px);
  }
  75%,
  100% {
    opacity: 1;
    transform: translate(0, 0);
  }
}
@keyframes path-team {
  0% {
    opacity: 0;
    transform: translate(90px, 150px);
  }
  45%,
  52% {
    opacity: 1;
    transform: translate(-150px, -16px);
  }
  62%,
  68% {
    transform: translate(-155px, 46px);
  }
  92%,
  100% {
    opacity: 1;
    transform: translate(0, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .scene *,
  .scene :deep(*) {
    animation: none !important;
    transition: none !important;
  }
  .scene .frag:hover {
    translate: none;
    scale: none;
  }
  .scene .frag::after {
    transition: none;
  }
}
</style>
