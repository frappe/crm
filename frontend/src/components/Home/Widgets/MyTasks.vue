<template>
  <HomeWidget
    :title="__('My tasks')"
    :resource="resource"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="__('No tasks on your list.')"
    emptyIcon="lucide-square-check"
  >
    <template #default="{ rows }">
      <TaskRow
        v-for="task in rows"
        :key="task.name"
        :task="task"
        @open="openTask"
      />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import TaskRow from '@/components/Home/TaskRow.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { refreshHome, useHomeWidget } from '@/composables/homeWidget'

// Home passes `config` to every widget; declared so it does not fall through as a setting
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
