<template>
  <HomeWidget
    :title="__('Upcoming follow-ups')"
    :resource="resource"
    widget="upcoming_follow_ups"
    :columns="defaultColumns"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No follow-ups in the next 7 days.')"
    emptyIcon="lucide-calendar"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows, columns }">
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

const defaultColumns = [
  homeColumns.task(),
  homeColumns.taskRecord(),
  homeColumns.dueDate(),
]

const resource = useHomeWidget('upcoming_follow_ups', () => props.config)
</script>
