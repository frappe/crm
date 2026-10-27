<template>
  <HomeWidget
    :title="__('Team overdue follow-ups')"
    :resource="resource"
    :config="config"
    :viewAll="{ name: 'Tasks' }"
    :emptyText="__('Your team has no follow-ups overdue in the last 30 days.')"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="taskRecordRoute" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useHomeWidget } from '@/composables/homeWidget'
import { taskRecordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.task(),
  homeColumns.taskRecord(),
  homeColumns.dueDate(),
  homeColumns.priority(),
  homeColumns.user('assigned_to', __('Assigned to')),
]

const resource = useHomeWidget('team_overdue_follow_ups', () => props.config)
</script>
