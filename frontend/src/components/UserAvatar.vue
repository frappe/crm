<template>
<<<<<<< HEAD
  <Avatar
    :label="getUser(user).full_name"
    :image="getUser(user).user_image"
    v-bind="$attrs"
  />
=======
  <span class="relative inline-flex shrink-0" :class="marginClasses">
    <Avatar
      :label="getUser(user).full_name"
      :image="getUser(user).user_image"
      v-bind="avatarAttrs"
    />
    <AvailabilityDot
      v-if="!hideStatus"
      :user="user"
      class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
      :class="dotSize"
    />
  </span>
>>>>>>> 19fa04a (fix: keep the availability dot inside the avatar so list cells don't clip it)
</template>
<script setup>
import { usersStore } from '@/stores/users'
import { Avatar } from 'frappe-ui'

defineProps({
  user: { type: String, default: null },
})

const { getUser } = usersStore()
</script>
