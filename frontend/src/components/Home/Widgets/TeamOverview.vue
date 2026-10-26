<template>
  <HomeWidget
    :title="__('Team overview')"
    :resource="resource"
    :emptyText="__('No one is on your team yet.')"
    emptyIcon="lucide-users"
  >
    <template #default="{ rows }">
      <div class="grid text-base" :style="{ gridTemplateColumns: columns }">
        <div
          class="contents text-sm text-ink-gray-5 [&>*]:sticky [&>*]:top-0 [&>*]:bg-surface-elevation-2 [&>*]:py-1.5"
        >
          <span class="px-2">{{ __('Member') }}</span>
          <span v-for="stat in stats" :key="stat.key" class="px-2 text-right">
            {{ stat.label }}
          </span>
        </div>
        <div
          v-for="row in sorted(rows)"
          :key="row.user"
          class="contents [&>*]:flex [&>*]:h-8 [&>*]:items-center [&>*]:border-t [&>*]:border-outline-gray-1"
        >
          <span class="min-w-0 gap-2 px-2">
            <UserAvatar :user="row.user" size="sm" hideStatus />
            <span class="truncate text-ink-gray-8">
              {{ getUser(row.user).full_name }}
            </span>
          </span>
          <span
            v-for="stat in stats"
            :key="stat.key"
            class="justify-end px-2 tabular-nums"
            :class="row[stat.key] ? 'text-ink-gray-8' : 'text-ink-gray-4'"
          >
            {{ stat.format ? stat.format(row[stat.key]) : row[stat.key] }}
          </span>
        </div>
      </div>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { shortDuration } from '@/utils/home'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const { getUser } = usersStore()

const stats = [
  { key: 'open', label: __('Open') },
  { key: 'replies_waiting', label: __('Replies waiting') },
  { key: 'overdue_follow_ups', label: __('Overdue follow-ups') },
  { key: 'no_next_step', label: __('No next step') },
  {
    key: 'first_response_time',
    label: __('Avg. first response'),
    format: (seconds) => shortDuration(seconds) || '—',
  },
]

const columns = `minmax(10rem, 1fr) repeat(${stats.length}, minmax(5rem, auto))`

const resource = useHomeWidget('team_overview')

function sorted(rows) {
  const name = (row) => getUser(row.user).full_name || row.user
  return [...rows].sort((a, b) => name(a).localeCompare(name(b)))
}
</script>
