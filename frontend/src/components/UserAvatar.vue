<template>
  <Avatar
    v-if="user"
    :label="getUser(user).full_name"
    :image="getUser(user).user_image"
    v-bind="$attrs"
  />
</template>
<script setup>
import { Avatar } from 'frappe-ui'
import { usersStore } from '@/stores/users'

const props = defineProps({
  user: {
    type: String,
    default: null,
  },
})

const { getUser } = usersStore()
</script>
