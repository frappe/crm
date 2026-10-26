<template>
  <HomeWidget
    :title="__('Follow-ups due')"
    :resource="resource"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('Nothing due today. You are all caught up.')"
    :columns="['1rem', 'minmax(0,1fr)', '6rem', '3.5rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <TaskRow :task="row">
        <ListCell class="justify-end">
          <FollowUpActions class="relative" :task="row" @change="refreshHome" />
        </ListCell>
      </TaskRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import FollowUpActions from '@/components/FollowUp/FollowUpActions.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'
import { ListCell } from 'frappe-ui/list'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('follow_ups_due', () => props.config)
</script>
