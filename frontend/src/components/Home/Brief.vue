<template>
  <section :aria-label="__('Today\'s brief')" class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <div class="flex min-w-0 items-baseline gap-2">
        <h2 class="text-xl-semibold text-ink-gray-9">
          {{ __("Today's brief") }}
        </h2>
        <span class="flex items-baseline gap-1 text-base text-ink-gray-5">
          {{ __('on') }}
          <PeriodPicker
            :period="doctype"
            :labels="RECORD_LABELS"
            @change="(value) => emit('update:doctype', value)"
          />
        </span>
      </div>
      <HomeTabs
        v-if="isManager()"
        v-model="tab"
        :tabs="tabs"
        :counts="shownCounts"
      />
    </div>

    <ol
      v-if="!loaded"
      :aria-label="__('Loading')"
      class="divide-y divide-outline-gray-2 rounded-4 border border-outline-gray-2 bg-surface-elevation-2"
    >
      <li
        v-for="row in PLACEHOLDER_ROWS"
        :key="row"
        class="flex h-[60px] animate-pulse items-center gap-3 pl-3.5 pr-3"
      >
        <span class="size-7 shrink-0 rounded-4 bg-surface-gray-2" />
        <div class="flex flex-1 flex-col gap-2">
          <span class="h-3 w-1/3 rounded bg-surface-gray-2" />
          <span class="h-2.5 w-1/2 rounded bg-surface-gray-2" />
        </div>
      </li>
    </ol>
    <div
      v-else-if="!items.length"
      class="flex min-h-[180px] flex-col items-center justify-center gap-3 rounded-4 border border-outline-gray-2 bg-surface-elevation-2 p-6 text-center"
    >
      <span
        aria-hidden="true"
        class="flex size-7 items-center justify-center rounded-4 bg-surface-gray-2 text-ink-gray-7"
      >
        <span class="lucide-check-check size-4" />
      </span>
      <div class="flex flex-col items-center gap-1">
        <span class="text-base-medium text-ink-gray-9">
          {{ __("You're all caught up") }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ emptyLine.text }}
          <button
            v-if="emptyLine.team"
            type="button"
            class="text-ink-gray-8 underline underline-offset-2 hover:text-ink-gray-9"
            @click="tab = 'team'"
          >
            {{ __('View team') }}
          </button>
        </span>
      </div>
    </div>
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
        </div>
      </li>
    </ol>
    <p v-if="loaded && footerLinks.length" class="text-sm text-ink-gray-6">
      <template v-for="(link, index) in footerLinks" :key="link.label">
        <span v-if="index" aria-hidden="true"> · </span>
        <router-link
          :to="link.route"
          class="text-ink-gray-8 underline underline-offset-2 hover:text-ink-gray-9"
        >
          {{ link.label }}
        </router-link>
      </template>
    </p>
  </section>
</template>
<script setup>
import BriefAction from '@/components/Home/BriefAction.vue'
import HomeTabs from '@/components/Home/HomeTabs.vue'
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { usersStore } from '@/stores/users'
import {
  briefAge,
  briefBadge,
  briefCount,
  briefDetail,
  briefEmptyLine,
  briefIcon,
  briefMoreLinks,
  briefOlderLinks,
  briefPerson,
  briefRoute,
  briefTitle,
} from '@/utils/brief'
import { formatDate } from '@/utils'
import { RECORD_LABELS } from '@/utils/home'
import { formatTaskDue } from '@/utils/task'
import { Avatar, Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  resource: { type: Object, required: true },
  counts: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:doctype'])

const tab = defineModel('tab', { type: String, required: true })

const { getUser, isManager } = usersStore()

const doctype = computed(() => props.resource.data?.doctype || 'Both')

const shownCounts = computed(() =>
  Object.fromEntries(
    Object.entries(props.counts).map(([name, count]) => [
      name,
      briefCount(count),
    ]),
  ),
)

const tabs = [
  { label: __('Team'), value: 'team' },
  { label: __('For you'), value: 'mine' },
]

// As many rows as the Brief shows at most
const PLACEHOLDER_ROWS = 5

const loaded = computed(() => props.resource.data?.tab === tab.value)

const items = computed(() => props.resource.data?.items || [])

const emptyLine = computed(() =>
  briefEmptyLine({
    tab: tab.value,
    isManager: isManager(),
    counts: props.counts,
    older: props.resource.data?.older,
  }),
)

const footerLinks = computed(() => [
  ...briefMoreLinks(props.resource.data?.more),
  ...briefOlderLinks(props.resource.data),
])

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
