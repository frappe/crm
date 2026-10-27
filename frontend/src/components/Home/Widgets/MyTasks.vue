<template>
  <HomeWidget
    :title="__('My tasks')"
    :resource="resource"
    widget="my_tasks"
    :columns="defaultColumns"
    :config="config"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No tasks on your list.')"
    emptyIcon="lucide-square-check"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows, columns }">
      <HomeTable :columns="columns" :rows="rows" :onRowClick="openTask" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const { showModal } = useDoctypeModal()

const defaultColumns = [
  homeColumns.taskStatus(),
  homeColumns.task(),
  homeColumns.priority(),
  homeColumns.dueDate(),
]

const resource = useHomeWidget('my_tasks', () => props.config)

function openTask(task) {
  showModal({
    name: task.name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: { afterUpdate: refreshHome },
  })
}
</script>
