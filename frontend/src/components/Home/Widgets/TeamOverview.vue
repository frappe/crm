<template>
  <HomeWidget
    :title="__('Team overview')"
    :resource="resource"
    :emptyText="__('No one is on your team yet.')"
    emptyIcon="lucide-users"
  >
    <template #list="{ rows }">
      <List :columns="columns" :rowHeight="32" class="list-row-px-2 text-base">
        <ListHeader class="sticky top-0 z-10 bg-surface-elevation-2">
          <ListHeaderCell>{{ __('Member') }}</ListHeaderCell>
          <ListHeaderCell
            v-for="stat in stats"
            :key="stat.key"
            class="justify-end"
          >
            {{ stat.label }}
          </ListHeaderCell>
        </ListHeader>
        <ListRows :items="visible(rows)" rowKey="user" v-slot="{ item }">
          <ListRow>
            <ListCell class="gap-2">
              <UserAvatar :user="item.user" size="sm" hideStatus />
              <span class="truncate text-ink-gray-8">
                {{ getUser(item.user).full_name }}
              </span>
            </ListCell>
            <ListCell
              v-for="stat in stats"
              :key="stat.key"
              class="justify-end tabular-nums"
              :class="item[stat.key] ? 'text-ink-gray-8' : 'text-ink-gray-4'"
            >
              {{ stat.format ? stat.format(item[stat.key]) : item[stat.key] }}
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
    </template>
    <template v-if="members.length > VISIBLE_MEMBERS" #footer>
      <Button
        variant="ghost"
        :label="
          expanded ? __('Show less') : __('Show all {0}', [members.length])
        "
        :iconRight="expanded ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        @click="expanded = !expanded"
      />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { shortDuration } from '@/utils/home'
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'
import { computed, ref } from 'vue'

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

const columns = ['minmax(10rem,1fr)', ...stats.map(() => 'minmax(5rem,9rem)')]

// Fits the default card height (see widgets.js); the rest scroll once expanded.
const VISIBLE_MEMBERS = 9

const resource = useHomeWidget('team_overview')

const expanded = ref(false)

const members = computed(() => resource.data?.rows || [])

function visible(rows) {
  const busiestFirst = [...rows].sort(
    (a, b) => b.open - a.open || name(a).localeCompare(name(b)),
  )
  return expanded.value ? busiestFirst : busiestFirst.slice(0, VISIBLE_MEMBERS)
}

function name(row) {
  return getUser(row.user).full_name || row.user
}
</script>
