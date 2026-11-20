<template>
  <div class="flex flex-col gap-2">
    <h1 class="text-2xl-semibold leading-none text-ink-gray-9">
      {{ greeting }}
    </h1>
    <p v-if="summary" class="text-p-base text-ink-gray-6">{{ summary }}</p>
  </div>
</template>

<script setup>
import { usersStore } from '@/stores/users'
import { briefSummary } from '@/utils/brief'
import { greetingFor } from '@/utils/home'
import { computed } from 'vue'

const props = defineProps({
  count: { type: Number, default: null },
  team: { type: Boolean, default: false },
  flow: { type: Boolean, default: false },
})

const { getUser } = usersStore()

const greeting = computed(() => {
  const name = getUser().first_name || getUser().full_name
  return greetingFor(new Date(), name)
})

const summary = computed(() =>
  props.count === null ? '' : briefSummary(props),
)
</script>
