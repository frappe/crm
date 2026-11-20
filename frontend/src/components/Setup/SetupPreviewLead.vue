<template>
  <div class="flex h-full flex-col">
    <header
      class="flex h-[42px] shrink-0 items-center justify-between border-b border-outline-gray-1 px-5"
    >
      <div class="flex items-center gap-1 text-lg">
        <span class="text-ink-gray-5">{{ __('Leads') }}</span>
        <span class="text-ink-gray-4">/</span>
        <span class="text-ink-gray-9">{{ SAMPLE_LEAD.name }}</span>
      </div>
      <div class="flex items-center gap-2">
        <Button :label="__('New')" tabindex="-1">
          <template #prefix>
            <StatusDot class="text-ink-gray-5" />
          </template>
        </Button>
        <Button variant="solid" :label="__('Convert to deal')" tabindex="-1" />
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <div class="flex min-w-0 flex-1 flex-col">
        <div
          class="flex h-10 shrink-0 items-end gap-5 border-b border-outline-gray-1 px-5"
        >
          <span
            v-for="tab in TABS"
            :key="tab.label"
            class="-mb-px flex items-center gap-1.5 border-b pb-2.5 text-base"
            :class="
              tab.active
                ? 'border-outline-gray-9 text-ink-gray-9'
                : 'border-transparent text-ink-gray-5'
            "
          >
            <span :class="[tab.icon, 'size-4']" />{{ __(tab.label) }}
          </span>
        </div>
        <div class="flex items-center justify-between px-8 pb-2 pt-5">
          <span class="text-lg font-medium text-ink-gray-9">
            {{ __('Emails') }}
          </span>
          <Button
            variant="ghost"
            icon-left="lucide-plus"
            :label="__('New Email')"
            tabindex="-1"
          />
        </div>
        <div class="relative flex-1 px-8">
          <Transition v-bind="swap">
            <div v-if="connected" key="email" class="flex gap-3 pt-2">
              <Avatar
                :label="SAMPLE_LEAD.name"
                :image="avatarUrl(SAMPLE_LEAD.name)"
                size="md"
                class="mt-1"
              />
              <div
                class="min-w-0 flex-1 rounded-6 border border-outline-gray-2 p-3"
              >
                <div class="flex items-center gap-2">
                  <span class="text-base font-medium text-ink-gray-9">
                    {{ SAMPLE_LEAD.name }}
                  </span>
                  <span class="ms-auto text-sm text-ink-gray-5">
                    {{ __('now') }}
                  </span>
                  <span
                    v-for="icon in EMAIL_ACTIONS"
                    :key="icon"
                    :class="[icon, 'size-4 text-ink-gray-6']"
                  />
                </div>
                <div class="mt-0.5 truncate text-sm text-ink-gray-5">
                  {{ __('To') }}: {{ state.email }}
                </div>
                <div class="mt-3 text-base font-semibold text-ink-gray-9">
                  {{ SAMPLE_LEAD.subject }}
                </div>
                <div class="mt-2 space-y-2 text-p-base text-ink-gray-8">
                  <p v-for="(p, i) in SAMPLE_LEAD.message" :key="i">{{ p }}</p>
                </div>
              </div>
            </div>
            <div
              v-else
              key="empty"
              class="flex flex-col items-center justify-center gap-3 pt-24 text-ink-gray-4"
            >
              <span class="lucide-mail size-10" />
              <span class="text-lg font-medium">
                {{ __('No Email Communications') }}
              </span>
              <Button :label="__('New Email')" tabindex="-1" />
            </div>
          </Transition>
        </div>
      </div>

      <aside
        class="flex w-[300px] shrink-0 flex-col border-l border-outline-gray-1"
      >
        <div class="flex items-center gap-3 border-b border-outline-gray-1 p-5">
          <Avatar
            :label="SAMPLE_LEAD.name"
            :image="avatarUrl(SAMPLE_LEAD.name)"
            size="3xl"
          />
          <div class="flex min-w-0 flex-col gap-2">
            <span class="truncate text-2xl font-medium text-ink-gray-9">
              {{ SAMPLE_LEAD.name }}
            </span>
            <div class="flex gap-1.5">
              <Button
                v-for="icon in QUICK_ACTIONS"
                :key="icon"
                :icon="icon"
                size="sm"
                tabindex="-1"
              />
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-3 p-5 text-base">
          <span class="font-medium text-ink-gray-9">{{ __('Details') }}</span>
          <div
            v-for="row in details"
            :key="row.label"
            class="flex items-center gap-2"
          >
            <span class="w-24 shrink-0 text-ink-gray-5">
              {{ __(row.label) }}
            </span>
            <span class="truncate text-ink-gray-8">{{ row.value }}</span>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import {
  SAMPLE_LEAD,
  StatusDot,
  avatarUrl,
} from '@/components/Setup/setupPreviewData'
import { usersStore } from '@/stores/users'
import { Avatar, Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  state: { type: Object, required: true },
})

const { getUser } = usersStore()

const connected = computed(() => !!(props.state.provider && props.state.email))

const TABS = [
  { label: 'Activity', icon: 'lucide-activity' },
  { label: 'Emails', icon: 'lucide-mail', active: true },
  { label: 'Comments', icon: 'lucide-message-square' },
  { label: 'Data', icon: 'lucide-list' },
  { label: 'Tasks', icon: 'lucide-square-check' },
  { label: 'Notes', icon: 'lucide-notepad-text' },
]
const EMAIL_ACTIONS = ['lucide-reply', 'lucide-reply-all']
const QUICK_ACTIONS = [
  'lucide-phone',
  'lucide-mail',
  'lucide-link',
  'lucide-paperclip',
]

const details = computed(() => [
  { label: 'Organization', value: SAMPLE_LEAD.organization },
  { label: 'Email', value: SAMPLE_LEAD.email },
  { label: 'Status', value: __('New') },
  { label: 'Lead owner', value: getUser()?.full_name },
])

const swap = {
  enterActiveClass:
    'transition duration-700 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none',
  enterFromClass: 'opacity-0 -translate-y-3',
  leaveActiveClass:
    'absolute inset-x-8 top-0 transition duration-150 motion-reduce:transition-none',
  leaveToClass: 'opacity-0',
}
</script>
