<template>
  <HomeWidget
    :title="__('Tasks')"
    :resource="resource"
    :viewAll="[{ label: __('Tasks'), route: { name: 'Tasks' } }]"
    :emptyText="emptyText[tab]"
    emptyIcon="lucide-square-check"
  >
    <template #tabs>
      <TabButtons v-model="tab" :options="tabs">
        <template #suffix="{ button }">
          <span
            v-if="counts[button.value]"
            class="text-sm tabular-nums text-ink-gray-5"
          >
            {{ counts[button.value] }}
          </span>
        </template>
      </TabButtons>
    </template>
    <template #default="{ rows }">
      <HomeTable
        :columns="columns"
        :rows="rows"
        :rowRoute="linkedRecordRoute"
        :onRowClick="openUnlinkedTask"
      >
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
import { useDoctypeModal } from '@/composables/doctypeModal'
import { homeVersion, refreshHome } from '@/composables/homeWidget'
import { taskRecordRoute } from '@/utils/home'
import { TabButtons, createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

// Declared so Home's `config` does not fall through to HomeWidget and show the doctype setting
defineProps({ config: { type: Object, default: null } })

const { showModal } = useDoctypeModal()

const tabs = [
  { label: __('All'), value: 'all' },
  { label: __('Due'), value: 'due' },
  { label: __('Upcoming'), value: 'upcoming' },
  { label: __('Unlinked'), value: 'unlinked' },
]

const emptyText = {
  all: __('No open tasks. You are all caught up.'),
  due: __('Nothing due today. You are all caught up.'),
  upcoming: __('Nothing due in the next 7 days.'),
  unlinked: __('No tasks outside your leads and deals.'),
}

const columns = [
  homeColumns.taskStatus(),
  homeColumns.task(),
  homeColumns.taskRecord(),
  homeColumns.priority(),
  homeColumns.dueDate(true),
  { key: 'actions', label: '', width: '3.5rem' },
]

const tab = ref('all')

const resource = createResource({
  url: 'crm.api.home.get_tasks',
  makeParams: () => ({ tab: tab.value }),
  auto: true,
})
watch([homeVersion, tab], () => resource.reload())

const counts = computed(() => resource.data?.counts || {})

function linkedRecordRoute(task) {
  return task.reference_docname ? taskRecordRoute(task) : null
}

function openUnlinkedTask(task) {
  if (task.reference_docname) return
  showModal({
    name: task.name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: { afterUpdate: refreshHome },
  })
}
</script>
