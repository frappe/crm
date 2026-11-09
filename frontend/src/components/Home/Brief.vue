<template>
  <section :aria-label="__('Today\'s brief')" class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <div class="flex items-baseline gap-2.5">
        <h2 class="text-xl-semibold text-ink-gray-9">
          {{ __("Today's brief") }}
        </h2>
        <span class="text-sm text-ink-gray-5">
          {{
            tab === 'team'
              ? __('The most urgent items across your team')
              : __('Your most urgent items')
          }}
        </span>
      </div>
      <HomeTabs
        v-if="isManager()"
        v-model="tab"
        :tabs="tabs"
        :counts="resource.data?.counts"
      />
    </div>

    <div
      v-if="resource.loading && !items.length"
      class="flex justify-center py-6"
    >
      <LoadingIndicator class="size-4 text-ink-gray-5" />
    </div>
    <HomeEmptyState
      v-else-if="!items.length"
      compact
      icon="lucide-check"
      class="rounded-4 border border-outline-gray-2 p-4"
      :text="__('Nothing needs you today')"
    />
    <ol
      v-else
      class="divide-y divide-outline-gray-2 rounded-4 border border-outline-gray-2 bg-surface-elevation-2"
    >
      <li
        v-for="item in items"
        :key="item.kind + (item.name || item.member || '')"
        class="grid h-[60px] grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-3 pl-3.5 pr-3"
      >
        <Avatar
          v-if="briefPerson(item)"
          size="xl"
          :label="fullName(briefPerson(item))"
          :image="getUser(briefPerson(item))?.user_image"
        />
        <span
          v-else
          aria-hidden="true"
          class="flex size-7 items-center justify-center rounded-4 bg-surface-gray-2 text-ink-gray-7"
        >
          <span :class="briefIcon(item)" class="size-4" />
        </span>
        <div class="flex min-w-0 flex-col gap-0.5">
          <div class="flex min-w-0 items-center gap-2">
            <router-link
              :to="briefRoute(item)"
              class="truncate text-base-medium text-ink-gray-9 hover:underline"
            >
              {{ briefTitle(item, { name: fullName }) }}
            </router-link>
            <Badge
              v-if="briefBadge(item)"
              class="shrink-0"
              :theme="briefBadge(item).theme"
              :label="briefBadge(item).label"
            />
          </div>
          <p
            v-if="detail(item)"
            class="truncate text-sm text-ink-gray-6"
            :title="detail(item)"
          >
            {{ detail(item) }}
          </p>
        </div>
        <div class="flex items-center gap-2.5">
          <span
            v-if="briefAge(item)"
            class="whitespace-nowrap text-sm"
            :class="briefAge(item).late ? 'text-ink-red-7' : 'text-ink-gray-5'"
          >
            {{ briefAge(item).label }}
          </span>
          <BriefAction :item="item" />
          <router-link
            :to="briefRoute(item)"
            :aria-label="__('Open')"
            class="flex text-ink-gray-5"
          >
            <span aria-hidden="true" class="lucide-chevron-right size-4" />
          </router-link>
        </div>
      </li>
    </ol>
  </section>
</template>
<script setup>
import BriefAction from '@/components/Home/BriefAction.vue'
import HomeEmptyState from '@/components/Home/HomeEmptyState.vue'
import HomeTabs from '@/components/Home/HomeTabs.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { usersStore } from '@/stores/users'
import {
  briefAge,
  briefBadge,
  briefDetail,
  briefIcon,
  briefPerson,
  briefRoute,
  briefTitle,
} from '@/utils/brief'
import { formatDate } from '@/utils'
import { formatTaskDue } from '@/utils/task'
import { Avatar, Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  resource: { type: Object, required: true },
})

const tab = defineModel('tab', { type: String, required: true })

const { getUser, isManager } = usersStore()

const tabs = [
  { label: __('Team'), value: 'team' },
  { label: __('For you'), value: 'mine' },
]

const items = computed(() => props.resource.data?.items || [])

function fullName(user) {
  return getUser(user)?.full_name || user
}

function detail(item) {
  return briefDetail(item, {
    name: fullName,
    formatDate: (date) => formatDate(date, 'D MMM'),
    formatDue: formatTaskDue,
  })
}
</script>
