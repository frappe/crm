<template>
  <HomeWidget
    :title="__('Assigned to me')"
    :resource="resource"
    :config="config"
    :viewAll="recordListViews(config.doctype)"
    :emptyText="__('Nothing open is assigned to you.')"
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
import { recordListViews, recordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.record(),
  homeColumns.status(),
  homeColumns.timeAgo('assigned_at', __('Assigned')),
]

const resource = useHomeWidget('assigned_to_me', () => props.config)
</script>
