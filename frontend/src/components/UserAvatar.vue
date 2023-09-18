<template>
  <Avatar
    v-if="user"
    :label="$user(user).full_name"
    :image="$user(user).user_image"
    v-bind="$attrs"
  />
</template>
<script setup>
import { Avatar } from 'frappe-ui'

const props = defineProps({
  user: {
    type: String,
    default: null,
  },
})
</script>
