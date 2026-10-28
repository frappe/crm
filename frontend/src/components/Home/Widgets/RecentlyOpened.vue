<template>
  <HomeWidget
    :title="__('Recent activity')"
    :subtitle="__('Leads and deals you worked on or opened in the last 7 days')"
    :resource="resource"
    :config="config"
    :emptyText="__('Leads and deals you work on will show up here.')"
    emptyIcon="lucide-history"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { recordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.record(),
  { key: 'activity', label: __('Activity'), width: 'minmax(0,2fr)' },
  homeColumns.timeAgo('at', __('When')),
]

const resource = useHomeWidget('recently_opened', () => props.config)
</script>
