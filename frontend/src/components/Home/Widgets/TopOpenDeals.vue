<template>
  <HomeWidget
    :title="__('Top open deals')"
    :subtitle="__('Your biggest open deals by value')"
    :resource="resource"
    :viewAll="{ name: 'Deals' }"
    :emptyText="__('No open deals with a value yet.')"
    emptyIcon="lucide-trophy"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute">
        <template #title="{ row }">
          <div class="flex min-w-0 items-center gap-2">
            <Avatar :image="row.logo" :label="row.title" size="sm" />
            <span class="truncate text-base">{{ row.title }}</span>
          </div>
        </template>
      </HomeTable>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { recordRoute } from '@/utils/home'
import { formatCompactNumber } from '@/utils/numberFormat'
import { Avatar } from 'frappe-ui'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const resource = useHomeWidget('top_open_deals')

const columns = [
  { ...homeColumns.record(), label: __('Deal') },
  homeColumns.status(),
  {
    key: 'value',
    label: __('Value'),
    width: '5rem',
    align: 'right',
    getLabel: ({ row }) =>
      `${resource.data?.currency || ''}${formatCompactNumber(row.value)}`,
  },
]
</script>
