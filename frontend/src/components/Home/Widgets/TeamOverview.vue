<template>
  <HomeWidget
    :title="__('Team workload')"
    :subtitle="__('Per person, for leads and deals created in the period')"
    :resource="resource"
    :emptyText="__('No one is on your team yet.')"
    emptyIcon="lucide-users"
  >
    <template #tabs>
      <PeriodPicker
        class="h-6 text-base"
        :period="config?.period"
        @change="(period) => emit('update:config', { ...config, period })"
      />
    </template>
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="visible(rows)">
        <template #first_response_time="{ column, row }">
          <Tooltip :text="slaHint(row)">
            <div
              class="truncate text-right text-base tabular-nums"
              :class="missedSla(row) ? 'text-ink-red-7' : 'text-ink-gray-8'"
            >
              {{ column.getLabel({ row }) }}
            </div>
          </Tooltip>
        </template>
      </HomeTable>
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
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { shortDuration } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { computed, ref } from 'vue'

// Not passed on to HomeWidget, which would show the doctype setting for any config
const props = defineProps({ config: { type: Object, default: null } })

const emit = defineEmits(['update:config'])

const { getUser } = usersStore()

// Stat columns are as wide as their short label, so Member keeps the rest of a half-width card.
const stat = (key, label, tooltip, width, format = String) => ({
  key,
  label,
  tooltip,
  width,
  align: 'right',
  getLabel: ({ row }) => format(row[key]),
})

const columns = [
  { ...homeColumns.user('user', __('Member')), width: 'minmax(0,1fr)' },
  stat('open', __('Open'), __('Open leads and deals'), '2.25rem'),
  stat('replies_waiting', __('Replies'), __('Awaiting reply'), '3rem'),
  stat('overdue_follow_ups', __('Overdue'), __('Overdue follow-ups'), '3.5rem'),
  stat(
    'no_next_step',
    __('Going cold'),
    __('Open leads and deals with no follow-up and no activity in 7 days'),
    '5rem',
  ),
  stat(
    'first_response_time',
    __('First response'),
    __('Average first response time, in red when an SLA was missed'),
    '6rem',
    (seconds) => shortDuration(seconds) || '—',
  ),
]

function missedSla(row) {
  return row.sla_met < row.sla_total
}

function slaHint(row) {
  if (!row.sla_total) return __('No SLA due in this period')
  const rate = Math.round((row.sla_met / row.sla_total) * 100)
  return __('SLA met on {0} of {1} ({2}%)', [row.sla_met, row.sla_total, rate])
}

// Fits the default card height (see widgets.js); the rest scroll once expanded.
const VISIBLE_MEMBERS = 6

const resource = useHomeWidget('team_overview', () => props.config || {})

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
