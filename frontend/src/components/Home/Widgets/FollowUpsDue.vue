<template>
  <HomeWidget
    :title="__('Follow-ups due')"
    :resource="resource"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('Nothing due today. You are all caught up.')"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows }">
      <TaskRow v-for="task in rows" :key="task.name" :task="task">
        <FollowUpActions :task="task" @change="refreshHome" />
      </TaskRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import FollowUpActions from '@/components/FollowUp/FollowUpActions.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('follow_ups_due', () => props.config)
</script>
