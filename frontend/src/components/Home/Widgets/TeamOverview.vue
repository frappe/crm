<template>
  <HomeWidget
    :title="__('Team workload')"
    :resource="resource"
    :emptyText="__('No team activity in this period.')"
    emptyIcon="lucide-users"
  >
    <template #subtitle>
      <div class="flex min-w-0 items-center gap-1 text-base text-ink-gray-5">
        <span class="truncate">{{ CREATED_IN[doctype] }}</span>
        <PeriodPicker
          class="h-5 shrink-0 text-base"
          :period="config?.period"
          @change="(period) => emit('update:config', { ...config, period })"
        />
      </div>
    </template>
    <template #tabs>
      <Filter
        :key="doctype"
        variant="outline"
        :modelValue="{ data: {}, params: { filters: config?.filters || {} } }"
        :doctype="doctype === 'Lead' ? 'CRM Lead' : 'CRM Deal'"
        :fields="doctype === 'Both' ? sharedFields : null"
        @update="(filters) => emit('update:config', { ...config, filters })"
      >
        <template #header>
          <div class="mb-3 flex items-center justify-between gap-4 px-2">
            <span class="text-base text-ink-gray-5">{{ __('Show') }}</span>
            <TabButtons
              :modelValue="doctype"
              :options="DOCTYPE_OPTIONS"
              @update:modelValue="setDoctype"
            />
          </div>
        </template>
      </Filter>
    </template>
    <template #default="{ rows }">
      <HomeTable v-model:sort="sort" :columns="columns" :rows="visible(rows)">
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
import Filter from '@/components/Filter.vue'
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { usersStore } from '@/stores/users'
import { fieldsOnBoth, filtersFor, shortDuration, sortRows } from '@/utils/home'
import { TabButtons, Tooltip, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({ config: { type: Object, default: null } })

const emit = defineEmits(['update:config'])

const { getUser } = usersStore()

const doctype = computed(() => props.config?.doctype || 'Both')

const CREATED_IN = {
  Both: __('Leads and deals created in'),
  Deal: __('Deals created in'),
  Lead: __('Leads created in'),
}

const DOCTYPE_OPTIONS = [
  { label: __('Both'), value: 'Both' },
  { label: __('Deals'), value: 'Deal' },
  { label: __('Leads'), value: 'Lead' },
]

const filterableFields = (doctype) =>
  createResource({
    url: 'crm.api.doc.get_filterable_fields',
    cache: ['filterableFields', doctype],
    params: { doctype },
    auto: true,
  })
const fieldsByDoctype = {
  Lead: filterableFields('CRM Lead'),
  Deal: filterableFields('CRM Deal'),
}

const sharedFields = computed(() =>
  fieldsOnBoth(fieldsByDoctype.Lead.data, fieldsByDoctype.Deal.data),
)

function setDoctype(value) {
  const fields =
    value === 'Both' ? sharedFields.value : fieldsByDoctype[value].data || []
  const filters = filtersFor(props.config?.filters, fields)
  emit('update:config', { ...props.config, doctype: value, filters })
}

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
  stat('open', __('Open'), __('Open leads and deals'), '3rem'),
  stat('replies_waiting', __('Replies'), __('Awaiting reply'), '3.75rem'),
  stat(
    'overdue_follow_ups',
    __('Overdue'),
    __('Overdue follow-ups'),
    '4.25rem',
  ),
  stat(
    'no_next_step',
    __('No next step'),
    __('Open leads and deals with no follow-up and no activity in 7 days'),
    '5.75rem',
  ),
  stat(
    'first_response_time',
    __('First response'),
    __('Average first response time, in red when an SLA was missed'),
    '6.75rem',
    (seconds) => shortDuration(seconds) || '—',
  ),
]

const sort = ref({ key: 'open', descending: true })

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
  const byName = rows
    .map((row) => ({ ...row, name: row.user }))
    .sort((a, b) => fullName(a).localeCompare(fullName(b)))
  const { key } = sort.value
  const sorted = sortRows(byName, sort.value, (row) =>
    key === 'user' ? fullName(row) : row[key],
  )
  return expanded.value ? sorted : sorted.slice(0, VISIBLE_MEMBERS)
}

function fullName(row) {
  return getUser(row.user).full_name || row.user
}
</script>
