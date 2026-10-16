<template>
  <span
    v-if="status"
    class="inline-block size-2 shrink-0 rounded-full"
    :class="availability.dotColor(status)"
  />
</template>

<script setup lang="ts">
import { availabilityStore } from '@/stores/availability'
import { computed } from 'vue'

const props = defineProps<{ user?: string; status?: string }>()

const availability = availabilityStore()

const status = computed(() =>
  props.status
    ? availability.getStatus(props.status)
    : availability.userStatus(props.user),
)
</script>
