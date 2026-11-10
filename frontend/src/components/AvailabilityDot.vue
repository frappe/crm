<template>
  <span
    v-if="status"
    class="inline-block size-2 shrink-0 rounded-full"
    :class="availability.dotColor(status)"
  />
</template>

<script setup lang="ts">
import { availabilityStore } from '@/stores/availability'
import { usersStore } from '@/stores/users'
import { computed } from 'vue'

const props = defineProps<{ user?: string; status?: string }>()

const availability = availabilityStore()
const { isCrmUser, getUser } = usersStore()

// contacts and other non-CRM emails also get avatars, they have no status
const status = computed(() => {
  if (props.status) return availability.getStatus(props.status)
  if (props.user && !isCrmUser(getUser(props.user).name)) return undefined
  return availability.userStatus(props.user)
})
</script>
