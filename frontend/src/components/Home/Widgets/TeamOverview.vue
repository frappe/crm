<template>
  <HomeWidget
    :title="__('Team workload')"
    :resource="resource"
    :emptyText="__('No one is on your team yet.')"
    emptyIcon="lucide-users"
  >
    <template #subtitle>
      <div class="flex min-w-0 items-center gap-1 text-base text-ink-gray-5">
        <span class="truncate">{{ __('Leads and deals created in') }}</span>
        <PeriodPicker
          class="h-5 shrink-0 text-base"
          :period="config?.period"
          @change="(period) => emit('update:config', { ...config, period })"
        />
      </div>
    </template>
    <template #tabs>
      <HomeTabs v-model="filter" :tabs="filters" :counts="filterCounts" />
    </template>
    <template #default="{ rows }">
      <HomeEmptyState
        v-if="!filtered(rows).length"
        compact
        class="flex-1 px-4"
        icon="lucide-check"
        :text="__('No one here right now.')"
      />
      <HomeTable v-else :columns="columns" :rows="visible(filtered(rows))">
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
import HomeEmptyState from '@/components/Home/HomeEmptyState.vue'
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeTabs from '@/components/Home/HomeTabs.vue'
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
    __('No next step'),
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

const filter = ref('everyone')

const filters = [
  { label: __('Everyone'), value: 'everyone' },
  { label: __('Over SLA'), value: 'over_sla' },
  { label: __('Overdue'), value: 'overdue' },
]

const filterRules = {
  everyone: () => true,
  over_sla: (row) => missedSla(row),
  overdue: (row) => row.overdue_follow_ups > 0,
}

const filterCounts = computed(() =>
  Object.fromEntries(
    Object.entries(filterRules).map(([key, rule]) => [
      key,
      members.value.filter(rule).length,
    ]),
  ),
)

function filtered(rows) {
  return rows.filter(filterRules[filter.value])
}

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
