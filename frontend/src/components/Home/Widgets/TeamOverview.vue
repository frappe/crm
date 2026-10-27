<template>
  <HomeWidget
    :title="__('Team overview')"
    :resource="resource"
    :emptyText="__('No one is on your team yet.')"
    emptyIcon="lucide-users"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="visible(rows)" showHeader />
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
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { shortDuration } from '@/utils/home'
import { computed, ref } from 'vue'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const { getUser } = usersStore()

const stat = (key, label, format = String) => ({
  key,
  label,
  align: 'right',
  width: 'minmax(5rem,9rem)',
  getLabel: ({ row }) => format(row[key]),
})

const columns = [
  { ...homeColumns.user('user', __('Member')), width: 'minmax(10rem,1fr)' },
  stat('open', __('Open')),
  stat('replies_waiting', __('Replies waiting')),
  stat('overdue_follow_ups', __('Overdue follow-ups')),
  stat('no_next_step', __('No next step')),
  stat(
    'first_response_time',
    __('Avg. first response'),
    (seconds) => shortDuration(seconds) || '—',
  ),
]

// Fits the default card height (see widgets.js); the rest scroll once expanded.
const VISIBLE_MEMBERS = 9

const resource = useHomeWidget('team_overview')

const expanded = ref(false)

const members = computed(() => resource.data?.rows || [])

function visible(rows) {
  const busiestFirst = rows
    .map((row) => ({ ...row, name: row.user }))
    .sort((a, b) => b.open - a.open || fullName(a).localeCompare(fullName(b)))
  return expanded.value ? busiestFirst : busiestFirst.slice(0, VISIBLE_MEMBERS)
}

function fullName(row) {
  return getUser(row.user).full_name || row.user
}
</script>
