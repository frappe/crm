<template>
  <Avatar
    :label="getUser(user).full_name"
    :image="getUser(user).user_image"
    v-bind="$attrs"
  />
</template>
<script setup>
import { usersStore } from '@/stores/users'
import { Avatar } from 'frappe-ui'

defineProps({
  user: { type: String, default: null },
})

const { getUser } = usersStore()
</script>
