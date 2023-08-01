<template>
  <Dropdown :options="userDropdownOptions">
    <template v-slot="{ open }">
      <button
        class="flex w-full items-center space-x-2 rounded-md p-2 text-left"
        :class="open ? 'bg-gray-300' : 'hover:bg-gray-200'"
        v-if="user"
      >
        <Avatar
          :label="user.full_name"
          :image="user.user_image"
          size="md"
        />
        <span class="hidden text-base font-medium text-gray-900 sm:inline">
          {{ user.full_name }}
        </span>
        <FeatherIcon
          name="chevron-down"
          class="h-4 w-4 sm:inline"
          aria-hidden="true"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import { Dropdown, Avatar, FeatherIcon } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users';
import { computed } from 'vue'

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
