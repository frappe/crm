<template>
  <Tooltip :text="user ? getUser(user).full_name : __('No owner')">
    <span class="relative flex w-5 shrink-0 justify-center">
      <UserAvatar v-if="user" :user="user" size="sm" hideStatus />
    </span>
  </Tooltip>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { Tooltip } from 'frappe-ui'

defineProps({
  user: { type: String, default: null },
})

const { getUser } = usersStore()
</script>
