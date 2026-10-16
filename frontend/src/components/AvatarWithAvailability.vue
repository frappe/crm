<template>
  <div class="relative shrink-0">
    <UserAvatar :user="user" size="sm" />
    <AvailabilityDot
      :user="user"
      class="absolute -bottom-0.5 -right-0.5 ring-2 ring-[--surface-elevation-2]"
    />
  </div>
</template>

<script setup lang="ts">
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import UserAvatar from '@/components/UserAvatar.vue'

defineProps<{ user: string }>()
</script>
