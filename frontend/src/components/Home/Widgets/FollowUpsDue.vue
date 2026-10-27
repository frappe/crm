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
      <HomeTable :columns="columns" :rows="rows" :rowRoute="taskRecordRoute">
        <template #actions="{ row }">
          <div class="flex justify-end" @click.stop.prevent>
            <FollowUpActions :task="row" @change="refreshHome" />
          </div>
        </template>
      </HomeTable>
    </template>
  </HomeWidget>
</template>
<script setup>
import FollowUpActions from '@/components/FollowUp/FollowUpActions.vue'
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'
import { taskRecordRoute } from '@/utils/home'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const columns = [
  homeColumns.task(),
  homeColumns.taskRecord(),
  homeColumns.dueDate(true),
  { key: 'actions', label: '', width: '3.5rem' },
]

const resource = useHomeWidget('follow_ups_due', () => props.config)
</script>
