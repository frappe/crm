<template>
  <div class="flex flex-col gap-2 px-5 pb-2 pt-6">
    <h1 class="text-2xl-semibold leading-none text-ink-gray-9">
      {{ greeting }}
    </h1>
    <p class="flex flex-wrap items-center gap-1.5 text-p-base text-ink-gray-6">
      <template v-for="(part, index) in summary" :key="part.key">
        <span v-if="index" aria-hidden="true">·</span>
        <span :class="{ 'text-ink-gray-8': part.count }">
          {{ part.label }}
        </span>
      </template>
    </p>
  </div>
</template>

<script setup>
import { homeVersion } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { greetingFor } from '@/utils/home'
import { createResource } from 'frappe-ui'
import { computed, watch } from 'vue'

const { getUser } = usersStore()

const counts = createResource({
  url: 'crm.api.home.get_counts',
  auto: true,
  initialData: {},
})

watch(homeVersion, () => counts.reload())

const greeting = computed(() => {
  const name = getUser().first_name || getUser().full_name
  return greetingFor(new Date(), name)
})

const summary = computed(() => {
  const {
    replies_waiting = 0,
    follow_ups_due = 0,
    new_leads = 0,
  } = counts.data || {}
  return [
    {
      key: 'replies',
      count: replies_waiting,
      label:
        replies_waiting === 1
          ? __('1 reply waiting')
          : __('{0} replies waiting', [replies_waiting]),
    },
    {
      key: 'follow-ups',
      count: follow_ups_due,
      label:
        follow_ups_due === 1
          ? __('1 follow-up due')
          : __('{0} follow-ups due', [follow_ups_due]),
    },
    {
      key: 'leads',
      count: new_leads,
      label:
        new_leads === 1 ? __('1 new lead') : __('{0} new leads', [new_leads]),
    },
  ]
})
</script>
