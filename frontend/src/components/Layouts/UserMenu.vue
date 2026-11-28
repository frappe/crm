<!-- The avatar menu at the foot of the sidebar: the person's profile, availability, settings, theme and log out. -->
<template>
  <Dropdown :options="menu" side="top" align="start">
    <button
      type="button"
      class="flex h-9 w-full min-w-0 items-center rounded-4 pl-1 text-left transition hover:bg-surface-gray-2 focus-visible:ring-0 focus-visible:focus-ring"
      :aria-label="user.full_name"
    >
      <UserAvatar size="md" />
      <span
        class="min-w-0 truncate text-sm text-ink-gray-8 transition-all ease-in-out"
        :class="
          isCollapsed
            ? 'ml-0 w-0 overflow-hidden opacity-0'
            : 'ml-2 w-auto opacity-100'
        "
      >
        {{ user.full_name }}
      </span>
    </button>
  </Dropdown>
</template>

<script setup>
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { availabilityStore } from '@/stores/availability'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import {
  showSettings,
  activeSettingsPage,
  closeMobileSidebar,
} from '@/composables/settings'
import { Avatar, Dropdown, useColorScheme } from 'frappe-ui'
import { computed, h } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const { logout } = sessionStore()
const { getUser } = usersStore()
const { colorScheme, setColorScheme } = useColorScheme()
const availability = availabilityStore()

const user = computed(() => getUser() || {})

const menu = computed(() =>
  [
    [profileHeader()],
    [
      {
        label: __('My settings'),
        icon: 'lucide-circle-user',
        onClick: openProfileSettings,
      },
      themeRow(),
      availabilityRow(),
    ],
    [
      {
        label: __('Log out'),
        icon: 'lucide-log-out',
        theme: 'red',
        onClick: () => logout.submit(),
      },
    ],
  ].map((options) => ({ group: '', hideLabel: true, options })),
)

function openProfileSettings() {
  closeMobileSidebar(() => {
    activeSettingsPage.value = __('Profile')
    showSettings.value = true
  })
}

// The dot sits in a 16px box so the row's label lines up with the icon rows.
function statusDot(status) {
  return () =>
    h('span', { class: 'grid size-4 place-items-center' }, [
      h(AvailabilityDot, { status }),
    ])
}

function availabilityRow() {
  const current = availability.myStatus
  return {
    label: current ? __(current) : __('Availability'),
    icon: statusDot(current),
    condition: () => availability.enabledStatuses.length > 0,
    submenu: availability.enabledStatuses.map((status) => ({
      label: __(status.name),
      icon: statusDot(status.name),
      selected: status.name === current,
      onClick: () => availability.setMyStatus(status.name),
    })),
  }
}

function themeRow() {
  const schemes = [
    { value: 'light', label: __('Light'), icon: 'lucide-sun' },
    { value: 'dark', label: __('Dark'), icon: 'lucide-moon' },
    { value: 'system', label: __('System'), icon: 'lucide-monitor' },
  ]
  return {
    label: __('Theme'),
    icon: 'lucide-sun-moon',
    submenu: schemes.map((scheme) => ({
      label: scheme.label,
      icon: scheme.icon,
      selected: colorScheme.value === scheme.value,
      onClick: () => setColorScheme(scheme.value),
    })),
  }
}

// A disabled row cannot be selected; the inline cursor beats the wrapper's `cursor-not-allowed`.
function profileHeader() {
  const { full_name, user_image, email, name } = user.value
  return {
    label: full_name,
    disabled: true,
    slots: {
      item: () =>
        h(
          'div',
          {
            class: 'flex items-center gap-2 px-2 py-1.5',
            style: { cursor: 'default' },
          },
          [
            h(Avatar, { image: user_image, label: full_name, size: 'xl' }),
            h('div', { class: 'flex min-w-0 flex-col gap-0.5' }, [
              h(
                'div',
                { class: 'truncate text-sm font-semibold text-ink-gray-9' },
                full_name,
              ),
              h(
                'div',
                { class: 'truncate text-xs text-ink-gray-5' },
                email || name,
              ),
            ]),
          ],
        ),
    },
  }
}
</script>
