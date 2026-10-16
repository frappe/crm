<template>
  <aside
    class="relative overflow-hidden bg-surface-gray-2"
    aria-hidden="true"
    inert
  >
    <Transition name="preview-swap" mode="out-in">
      <SetupEmailPreview
        v-if="step === 'connect_email'"
        key="email"
        :provider="provider"
      />

      <div
        v-else-if="step === 'bring_leads'"
        key="leads"
        class="absolute inset-0"
      >
        <SetupPreviewWindow :active="__('Leads')" :top="120">
          <SetupPreviewList
            :title="__('Leads')"
            :rows="importing ? LEADS.slice(0, 3) : LEADS"
            :stagger="importing ? 160 : 40"
          />
        </SetupPreviewWindow>
        <div
          class="preview-lift preview-in absolute left-32 top-14 z-10 w-72 rounded-5 px-3 py-2.5"
        >
          <div class="flex items-center gap-2 text-base">
            <FileSpreadsheetIcon class="size-4 shrink-0 text-ink-gray-6" />
            <span class="truncate text-ink-gray-9">{{ importLabel }}</span>
            <span
              v-if="state.importRows"
              class="ml-auto shrink-0 text-sm tabular-nums text-ink-gray-5"
            >
              {{ __('{0} rows', [state.importRows]) }}
            </span>
          </div>
          <Progress
            v-if="importing"
            class="mt-2.5"
            size="sm"
            :value="importPercent"
          />
          <div
            v-else-if="state.importResult"
            class="mt-2 flex items-center gap-3 text-sm text-ink-gray-6"
          >
            <span class="flex items-center gap-1.5">
              <span class="size-1.5 rounded-full bg-surface-green-6" />
              {{ __('{0} imported', [state.importResult.imported]) }}
            </span>
            <span
              v-if="state.importResult.failed"
              class="flex items-center gap-1.5"
            >
              <span class="size-1.5 rounded-full bg-surface-amber-6" />
              {{ __('{0} failed', [state.importResult.failed]) }}
            </span>
          </div>
        </div>
      </div>

      <div
        v-else-if="step === 'invite_team'"
        key="team"
        class="absolute inset-0"
      >
        <SetupPreviewWindow :active="__('Deals')">
          <SetupPreviewList
            :title="__('Deals')"
            :last-label="__('Owner')"
            :rows="DEALS"
          />
        </SetupPreviewWindow>
        <div
          class="preview-lift preview-in absolute left-48 top-56 z-10 w-60 rounded-5 p-1.5"
          style="animation-delay: 120ms"
        >
          <div class="px-2 pb-1.5 pt-1 text-sm text-ink-gray-5">
            {{ __('Assign Globex renewal to') }}
          </div>
          <div
            v-for="member in TEAM"
            :key="member.name"
            class="flex items-center gap-2 rounded-4 px-2 py-1.5 text-base"
            :class="{ 'bg-surface-gray-2': member.selected }"
          >
            <Avatar :label="member.name" size="sm" />
            <span class="min-w-0 flex-1">
              <span class="block truncate text-ink-gray-9">{{
                member.name
              }}</span>
              <span class="block truncate text-sm text-ink-gray-5">
                {{ member.role }}
              </span>
            </span>
            <LucideCheck
              v-if="member.selected"
              class="size-4 text-ink-gray-7"
            />
          </div>
        </div>
      </div>

      <div
        v-else-if="step === 'about_you'"
        key="persona"
        class="absolute inset-0"
      >
        <SetupPreviewWindow :active="__('Leads')">
          <SetupPreviewList
            :title="__('Follow-ups due')"
            :rows="LEADS.slice(0, 5)"
          />
        </SetupPreviewWindow>
        <div
          class="preview-lift preview-in absolute left-8 top-72 z-10 w-60 rounded-5 bg-surface-gray-1 p-2"
          style="animation-delay: 120ms"
        >
          <SidebarLabel>{{ __('Suggested views') }}</SidebarLabel>
          <div class="flex flex-col gap-1">
            <SidebarItem
              v-for="view in VIEWS"
              :key="view.label"
              :label="view.label"
              :icon="view.icon"
              :suffix="view.count"
              :active="view.active"
            />
          </div>
        </div>
      </div>

      <div v-else key="done" class="absolute inset-0">
        <SetupPreviewWindow :active="__('Leads')">
          <SetupPreviewList :title="__('Leads')" :rows="LEADS" />
        </SetupPreviewWindow>
        <div
          class="preview-lift preview-in absolute left-44 top-48 z-10 w-64 rounded-5 p-3"
          style="animation-delay: 120ms"
        >
          <div class="flex items-center justify-between text-base">
            <span class="font-medium text-ink-gray-9">
              {{ __('Getting started') }}
            </span>
            <span class="text-sm tabular-nums text-ink-gray-5">
              {{ __('{0} of {1}', [doneCount, checklist.length]) }}
            </span>
          </div>
          <Progress
            class="mt-2"
            size="sm"
            :value="(doneCount / checklist.length) * 100"
          />
          <ul class="mt-2.5 flex flex-col gap-2 text-base">
            <li
              v-for="item in checklist"
              :key="item.label"
              class="flex items-center gap-2"
              :class="item.done ? 'text-ink-gray-5' : 'text-ink-gray-9'"
            >
              <component
                :is="item.done ? LucideCircleCheck : LucideCircle"
                class="size-4 text-ink-gray-6"
              />
              {{ item.label }}
            </li>
          </ul>
        </div>
      </div>
    </Transition>
  </aside>
</template>

<script setup>
import LucideCheck from '~icons/lucide/check'
import LucideCircle from '~icons/lucide/circle'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideAlarmClock from '~icons/lucide/alarm-clock'
import LucideGlobe from '~icons/lucide/globe'
import LucideUsers from '~icons/lucide/users'
import LucideHandshake from '~icons/lucide/handshake'
import FileSpreadsheetIcon from '@/components/Icons/FileSpreadsheetIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import SetupPreviewList from '@/components/Setup/SetupPreviewList.vue'
import SetupPreviewWindow from '@/components/Setup/SetupPreviewWindow.vue'
import SetupEmailPreview from '@/components/Setup/SetupEmailPreview.vue'
import { services } from '@/components/Settings/emailConfig'
import { Avatar, Progress, SidebarItem, SidebarLabel } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  step: { type: String, required: true },
  state: { type: Object, required: true },
  status: { type: Object, required: true },
})

const provider = computed(() =>
  services.find((service) => service.name === props.state.provider),
)

const importing = computed(() => props.state.importStage === 'importing')

const importPercent = computed(() => {
  const { current, total } = props.state.importProgress || {}
  return total ? Math.floor((current / total) * 100) : 10
})

const importLabel = computed(() => {
  if (!props.state.importStage) return __('Import a CSV or load sample data')
  return props.state.importFile || __('Upload a CSV file')
})

const checklist = computed(() => [
  { label: __('Connect your email'), done: isDone('connect_email') },
  { label: __('Import your leads'), done: isDone('bring_leads') },
  { label: __('Invite your team'), done: isDone('invite_team') },
  { label: __('Tell us about you'), done: isDone('about_you') },
  { label: __('Create your first deal'), done: false },
])

const doneCount = computed(
  () => checklist.value.filter((item) => item.done).length,
)

function isDone(step) {
  return props.status[step] === 'completed'
}

const LEADS = [
  { name: 'Priya Raman', status: 'New', when: 'now' },
  { name: 'Marcus Lee', status: 'Contacted', when: '2m' },
  { name: 'Ana Souza', status: 'Qualified', when: '5m' },
  { name: 'Kenji Ito', status: 'Nurture', when: '1h' },
  { name: 'Lena Fischer', status: 'New', when: '3h' },
  { name: 'Omar Haddad', status: 'Contacted', when: 'Tue' },
]

const DEALS = [
  { name: 'Globex renewal', status: 'Qualified', owner: 'Sam Patel' },
  { name: 'Initech pilot', status: 'Contacted', owner: 'Ria Kapoor' },
  { name: 'Umbrella expansion', status: 'Nurture', owner: 'Joe Mills' },
  { name: 'Hooli onboarding', status: 'New', owner: 'Sam Patel' },
  { name: 'Stark upsell', status: 'Contacted', owner: 'Ria Kapoor' },
]

const TEAM = [
  { name: 'Sam Patel', role: __('Sales Manager'), selected: true },
  { name: 'Ria Kapoor', role: __('Sales User') },
  { name: 'Joe Mills', role: __('Sales User') },
]

const VIEWS = [
  {
    label: __('Follow-ups due'),
    icon: LucideAlarmClock,
    count: '12',
    active: true,
  },
  { label: __('From website forms'), icon: LucideGlobe, count: '31' },
  { label: __('Referrals'), icon: LucideUsers, count: '8' },
  { label: __('Open deals'), icon: LucideHandshake, count: '5' },
]
</script>

<style scoped>
.preview-lift {
  background: var(--surface-base);
  border: 1px solid var(--outline-gray-3);
  box-shadow:
    0 1px 2px rgb(0 0 0 / 0.08),
    0 12px 32px -8px rgb(0 0 0 / 0.28);
}

.preview-in {
  animation: preview-fade-up 260ms ease-out both;
}

.preview-swap-enter-active,
.preview-swap-leave-active {
  transition: opacity 180ms ease;
}

.preview-swap-enter-from,
.preview-swap-leave-to {
  opacity: 0;
}

@keyframes preview-fade-up {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .preview-in {
    animation: none;
  }

  .preview-swap-enter-active,
  .preview-swap-leave-active {
    transition: none;
  }
}
</style>
