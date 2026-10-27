<template>
  <HomeWidget
    :title="__('My tasks')"
    :resource="resource"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No tasks on your list.')"
    emptyIcon="lucide-square-check"
  >
    <template #default="{ rows }">
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

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const { showModal } = useDoctypeModal()

const columns = [
  homeColumns.taskStatus(),
  homeColumns.task(),
  homeColumns.priority(),
  homeColumns.dueDate(),
]

const resource = useHomeWidget('my_tasks')

function openTask(task) {
  showModal({
    name: task.name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: { afterUpdate: refreshHome },
  })
}
</script>
