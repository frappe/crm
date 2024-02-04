<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showTaskModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    v-model="tasks"
    v-model:loadMore="loadMore"
    doctype="CRM Task"
  />
  <TasksListView
    v-if="tasks.data && rows.length"
    v-model="tasks.data.page_length_count"
    :rows="rows"
    :columns="tasks.data.columns"
    :options="{
      rowCount: tasks.data.row_count,
      totalCount: tasks.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @showTask="showTask"
    @reload="() => tasks.reload()"
  />
  <div v-else-if="tasks.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <EmailIcon class="h-10 w-10" />
      <span>No Tasks Found</span>
    </div>
  </div>
  <TaskModal v-model="showTaskModal" v-model:reloadTasks="tasks" :task="task" />
</template>

<script setup>
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import TasksListView from '@/components/ListViews/TasksListView.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import { usersStore } from '@/stores/users'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { Breadcrumbs } from 'frappe-ui'
import { computed, ref } from 'vue'

const breadcrumbs = [{ label: 'Tasks', route: { name: 'Tasks' } }]

const { getUser } = usersStore()

// tasks data is loaded in the ViewControls component
const tasks = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!tasks.value?.data?.data) return []
  return tasks.value?.data.data.map((task) => {
    let _rows = {}
    tasks.value?.data.rows.forEach((row) => {
      _rows[row] = task[row]

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(task[row], dateTooltipFormat),
          timeAgo: timeAgo(task[row]),
        }
      } else if (row == 'assigned_to') {
        _rows[row] = {
          label: task.assigned_to && getUser(task.assigned_to).full_name,
          ...(task.assigned_to && getUser(task.assigned_to)),
        }
      }
    })
    return _rows
  })
})

const showTaskModal = ref(false)

const task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
  reference_doctype: 'CRM Lead',
  reference_docname: '',
})

function showTask(name) {
  let t = rows.value?.find((row) => row.name === name)
  task.value = {
    title: t.title,
    description: t.description,
    assigned_to: t.assigned_to?.email || '',
    due_date: t.due_date,
    status: t.status,
    priority: t.priority,
    reference_doctype: t.reference_doctype,
    reference_docname: t.reference_docname,
  }
  showTaskModal.value = true
}
</script>
