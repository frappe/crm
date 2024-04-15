<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="tasksListView?.customListActions"
        :actions="tasksListView.customListActions"
      />
      <Button variant="solid" :label="__('Create')" @click="createTask">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="tasks"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Task"
  />
  <TasksListView
    ref="tasksListView"
    v-if="tasks.data && rows.length"
    v-model="tasks.data.page_length_count"
    v-model:list="tasks"
    :rows="rows"
    :columns="tasks.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: tasks.data.row_count,
      totalCount: tasks.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showTask="showTask"
    @applyFilter="(data) => viewControls.applyFilter(data)"
  />
  <div v-else-if="tasks.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <EmailIcon class="h-10 w-10" />
      <span>{{ __('No Tasks Found') }}</span>
      <Button :label="__('Create')" @click="showTaskModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <TaskModal v-model="showTaskModal" v-model:reloadTasks="tasks" :task="task" />
</template>

<script setup>
import CustomActions from '@/components/CustomActions.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import TasksListView from '@/components/ListViews/TasksListView.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import { usersStore } from '@/stores/users'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { Breadcrumbs } from 'frappe-ui'
import { computed, ref } from 'vue'

const breadcrumbs = [{ label: __('Tasks'), route: { name: 'Tasks' } }]

const { getUser } = usersStore()

const tasksListView = ref(null)

// tasks data is loaded in the ViewControls component
const tasks = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (!tasks.value?.data?.data) return []
  return tasks.value?.data.data.map((task) => {
    let _rows = {}
    tasks.value?.data.rows.forEach((row) => {
      _rows[row] = task[row]

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(task[row], dateTooltipFormat),
          timeAgo: __(timeAgo(task[row])),
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
  name: '',
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
    name: t.name,
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

function createTask() {
  task.value = {
    name: '',
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    status: 'Backlog',
    priority: 'Low',
    reference_doctype: 'CRM Lead',
    reference_docname: '',
  }
  showTaskModal.value = true
}
</script>
