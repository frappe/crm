<template>
  <HomeWidget
    :title="__('Team overdue follow-ups')"
    :resource="resource"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('Your team has no follow-ups overdue in the last 30 days.')"
    :columns="['1rem', 'minmax(0,1fr)', '6rem', '1.25rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <TaskRow :task="row">
        <ListCell>
          <OwnerAvatar :user="row.assigned_to" />
        </ListCell>
      </TaskRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import OwnerAvatar from '@/components/Home/OwnerAvatar.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { ListCell } from 'frappe-ui/list'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('team_overdue_follow_ups', () => props.config)
</script>
