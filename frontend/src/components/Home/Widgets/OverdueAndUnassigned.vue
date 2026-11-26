<template>
  <HomeWidget
    :title="__('Overdue and unassigned')"
    :subtitle="tabs[tab].subtitle"
    :resource="resource"
    :viewAll="tabs[tab].viewAll"
    :emptyText="tabs[tab].empty"
    :emptyIcon="tabs[tab].icon"
  >
    <template #tabs>
      <HomeTabs
        v-model="tab"
        :tabs="tabOptions"
        :counts="resource.data?.counts"
      />
    </template>
    <template #default="{ rows }">
      <HomeTable
        :columns="tabs[tab].columns"
        :rows="rows"
        :rowRoute="tabs[tab].route"
      />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeTabs from '@/components/Home/HomeTabs.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useTabbedHomeWidget } from '@/composables/homeWidget'
import { recordRoute, taskRecordRoute } from '@/utils/home'
import { ref } from 'vue'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting.
defineProps({ config: { type: Object, default: null } })

const tabs = {
  overdue: {
    subtitle: __('Team follow-ups past due in the last 30 days'),
    empty: __('Your team has no follow-ups overdue in the last 30 days.'),
    icon: 'lucide-calendar-check',
    viewAll: { name: 'Tasks' },
    route: taskRecordRoute,
    columns: [
      homeColumns.task(),
      homeColumns.user('assigned_to', __('Assigned to')),
      homeColumns.dueDate(),
    ],
  },
  unassigned: {
    subtitle: __('Open leads and deals nobody is assigned to'),
    empty: __('Every new lead and deal has an assignee.'),
    icon: 'lucide-user-check',
    viewAll: { name: 'Leads' },
    route: recordRoute,
    columns: [
      homeColumns.record(),
      homeColumns.status(),
      homeColumns.timeAgo('creation', __('Created')),
    ],
  },
}

const tabOptions = [
  { label: __('Overdue'), value: 'overdue' },
  { label: __('Unassigned'), value: 'unassigned' },
]

const tab = ref('overdue')

const resource = useTabbedHomeWidget('overdue_and_unassigned', tab)
</script>
