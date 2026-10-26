<template>
  <HomeWidget
    :title="__('My tasks')"
    :resource="resource"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No tasks on your list.')"
    emptyIcon="lucide-square-check"
    :columns="['1rem', 'minmax(0,1fr)', '6rem']"
  >
    <template #default="{ row }">
      <TaskRow :task="row" @open="openTask" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const { showModal } = useDoctypeModal()

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
