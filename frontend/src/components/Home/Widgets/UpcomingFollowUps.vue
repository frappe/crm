<template>
  <HomeWidget
    :title="__('Upcoming follow-ups')"
    :resource="resource"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No follow-ups in the next 7 days.')"
    emptyIcon="lucide-calendar"
    :columns="['1rem', 'minmax(0,1fr)', '6rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <TaskRow :task="row" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { useHomeWidget } from '@/composables/homeWidget'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('upcoming_follow_ups', () => props.config)
</script>
