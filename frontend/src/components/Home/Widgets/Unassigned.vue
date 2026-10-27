<template>
  <HomeWidget
    :title="__('Unassigned')"
    :resource="resource"
    :config="config"
    :viewAll="recordListRoute(config.doctype)"
    :emptyText="__('Every new lead and deal has an assignee.')"
    emptyIcon="lucide-user-check"
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
import { recordListRoute, recordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.record(),
  homeColumns.status(),
  homeColumns.timeAgo('creation', __('Created')),
]

const resource = useHomeWidget('unassigned', () => props.config)
</script>
