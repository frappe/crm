<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
  </LayoutHeader>
  <div class="flex justify-between items-center px-5 pb-2.5 border-b">
    <div class="flex items-center gap-2">
      <Button label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
      </Button>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
      </Button>
    </div>
    <div class="flex items-center gap-2">
      <Button icon="more-horizontal" />
    </div>
  </div>
  <ListView :list="list" :columns="columns" :rows="rows" row-key="name" />
</template>

<script setup>
import ListView from '@/components/ListView.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import { Button, createListResource } from 'frappe-ui'
import { computed } from 'vue'

const list = {
  title: 'Call Logs',
  plural_label: 'Call Logs',
  singular_label: 'Call Log',
}

const callLogs = createListResource({
  type: 'list',
  doctype: 'CRM Call Log',
  fields: [
    'from',
    'to',
    'duration',
    'start_time',
    'end_time',
    'status',
    'type',
    'recording_url',
    'modified',
  ],
  orderBy: 'modified desc',
  cache: 'Call Logs',
  pageLength: 999,
  auto: true,
})

const columns = [
  {
    label: 'From',
    key: 'from',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'To',
    key: 'to',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'Duration',
    key: 'duration',
    type: 'data',
    size: 'w-20',
  },
  {
    label: 'Type',
    key: 'type',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'Status',
    key: 'status',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'Start Time',
    key: 'start_time',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'End Time',
    key: 'end_time',
    type: 'data',
    size: 'w-32',
  },
  {
    label: 'Last modified',
    key: 'modified',
    type: 'pretty_date',
    size: 'w-28',
  },
]

const rows = computed(() => {
  return callLogs.data?.map((callLog) => {
    return {
      name: callLog.name,
      from: callLog.from,
      to: callLog.to,
      duration: callLog.duration,
      type: callLog.type,
      status: callLog.status,
      start_time: callLog.start_time,
      end_time: callLog.end_time,
      modified: callLog.modified,
    }
  })
})
</script>
