<template>
  <Dropdown :options="userDropdownOptions">
    <template v-slot="{ open }">
      <button
        class="flex w-full items-center rounded-md px-1 py-2 text-left"
        :class="open ? 'bg-gray-300' : 'hover:bg-gray-200'"
        v-if="user"
      >
        <UserAvatar class="flex-shrink-0" :user="user.name" size="md" />
        <span
          class="hidden text-base font-medium text-gray-900 sm:inline duration-300 ease-in-out"
          :class="isCollapsed ? 'opacity-0 ml-0' : 'opacity-100 ml-2'"
        >
          {{ user.full_name }}
        </span>
        <FeatherIcon
          name="chevron-down"
          class="h-4 w-4 sm:inline duration-300 ease-in-out"
          :class="isCollapsed ? 'opacity-0 ml-0' : 'opacity-100 ml-2'"
          aria-hidden="true"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { Dropdown, FeatherIcon } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

const { logout } = sessionStore()
const { getUser } = usersStore()

const user = computed(() => getUser() || {})

const userDropdownOptions = [
  {
    icon: 'log-out',
    label: 'Log out',
    onClick: () => logout.submit(),
  },
]
</script>
