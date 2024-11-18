<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="ToDos" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="todosListView?.customListActions"
        :actions="todosListView.customListActions"
      />
      <Button variant="solid" :label="__('Create')" @click="createToDo">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="todos"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="ToDo"
    :options="{
      allowedViews: ['list', 'kanban'],
    }"
  />
  <KanbanView
    v-if="$route.params.viewType == 'kanban' && rows.length"
    v-model="todos"
    :options="{
      onClick: (row) => showToDo(row.name),
      onNewClick: (column) => createToDo(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ titleField, itemName }">
      <div class="flex items-center gap-2">
        <div v-if="titleField === 'status'">
          <ToDoStatusIcon :status="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'priority'">
          <ToDoPriorityIcon :priority="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'allocated_to'">
          <Avatar
            v-if="getRow(itemName, titleField).full_name"
            class="flex items-center"
            :image="getRow(itemName, titleField).user_image"
            :label="getRow(itemName, titleField).full_name"
            size="sm"
          />
        </div>
        <div
          v-if="['modified', 'creation'].includes(titleField)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, titleField).label">
            <div>{{ getRow(itemName, titleField).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="getRow(itemName, titleField).label"
          class="truncate text-base"
        >
          {{ getRow(itemName, titleField).label }}
        </div>
        <div class="text-gray-500" v-else>{{ __('No Title') }}</div>
      </div>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <ToDoStatusIcon
            class="size-3"
            :status="getRow(itemName, fieldName).label"
          />
        </div>
        <div v-else-if="fieldName === 'priority'">
          <ToDoPriorityIcon :priority="getRow(itemName, fieldName).label" />
        </div>
        <div v-else-if="fieldName === 'allocated_to'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="sm"
          />
        </div>
        <div
          v-if="['modified', 'creation'].includes(fieldName)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="fieldName == 'description'"
          class="truncate text-base max-h-44"
        >
          <TextEditor
            v-if="getRow(itemName, fieldName).label"
            :content="getRow(itemName, fieldName).label"
            :editable="false"
            editor-class="!prose-sm max-w-none focus:outline-none"
            class="flex-1 overflow-hidden"
          />
        </div>
        <div v-else class="truncate text-base">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>
    <template #actions="{ itemName }">
      <div class="flex gap-2 items-center justify-between">
        <div>
          <Button
            class="-ml-2"
            v-if="getRow(itemName, 'reference_name').label"
            variant="ghost"
            size="sm"
            :label="
              getRow(itemName, 'reference_type').label == 'Opportunity'
                ? __('Opportunity')
                : __('Lead')
            "
            @click.stop="
              redirect(
                getRow(itemName, 'reference_type').label,
                getRow(itemName, 'reference_name').label,
              )
            "
          >
            <template #suffix>
              <ArrowUpRightIcon class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <Dropdown
          class="flex items-center gap-2"
          :options="actions(itemName)"
          variant="ghost"
          @click.stop.prevent
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </div>
    </template>
  </KanbanView>
  <ToDosListView
    ref="todosListView"
    v-else-if="todos.data && rows.length"
    v-model="todos.data.page_length_count"
    v-model:list="todos"
    :rows="rows"
    :columns="todos.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: todos.data.row_count,
      totalCount: todos.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showToDo="showToDo"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div v-else-if="todos.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <Email2Icon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('ToDos')]) }}</span>
      <Button :label="__('Create')" @click="showToDoModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <ToDoModal
    v-if="showToDoModal"
    v-model="showToDoModal"
    v-model:reloadToDos="todos"
    :todo="todo"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import ToDoStatusIcon from '@/components/Icons/ToDoStatusIcon.vue'
import ToDoPriorityIcon from '@/components/Icons/ToDoPriorityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import ToDosListView from '@/components/ListViews/ToDosListView.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import ToDoModal from '@/components/Modals/ToDoModal.vue'
import { usersStore } from '@/stores/users'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { Tooltip, Avatar, TextEditor, Dropdown, call } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const { getUser } = usersStore()

const router = useRouter()

const todosListView = ref(null)

// todos data is loaded in the ViewControls component
const todos = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object') {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

const rows = computed(() => {
  if (!todos.value?.data?.data) return []

  if (todos.value.data.view_type === 'kanban') {
    return getKanbanRows(todos.value.data.data)
  }

  return parseRows(todos.value?.data.data)
})

function getKanbanRows(data) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows)
}

function parseRows(rows) {
  return rows.map((todo) => {
    let _rows = {}
    todos.value?.data.rows.forEach((row) => {
      _rows[row] = todo[row]

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(todo[row], dateTooltipFormat),
          timeAgo: __(timeAgo(todo[row])),
        }
      } else if (row == 'allocated_to') {
        _rows[row] = {
          label: todo.allocated_to && getUser(todo.allocated_to).full_name,
          ...(todo.allocated_to && getUser(todo.allocated_to)),
        }
      }
    })
    return _rows
  })
}

const showToDoModal = ref(false)

const todo = ref({
  name: '',
  title: '',
  description: '',
  allocated_to: '',
  date: '',
  status: 'Backlog',
  priority: 'Low',
  reference_type: 'Lead',
  reference_name: '',
})

function showToDo(name) {
  let t = rows.value?.find((row) => row.name === name)
  todo.value = {
    name: t.name,
    title: t.title,
    description: t.description,
    allocated_to: t.allocated_to?.email || '',
    date: t.date,
    status: t.status,
    priority: t.priority,
    reference_type: t.reference_type,
    reference_name: t.reference_name,
  }
  showToDoModal.value = true
}

function createToDo(column) {
  todo.value = {
    name: '',
    title: '',
    description: '',
    allocated_to: '',
    date: '',
    status: 'Backlog',
    priority: 'Low',
    reference_type: 'Lead',
    reference_name: '',
  }

  if (column.column?.name) {
    let column_field = todos.value.params.column_field
    if (column_field) {
      todo.value[column_field] = column.column.name
    }
  }

  showToDoModal.value = true
}

function actions(name) {
  return [
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => {
        deleteToDo(name)
        todos.value.reload()
      },
    },
  ]
}

async function deleteToDo(name) {
  await call('frappe.client.delete', {
    doctype: 'ToDo',
    name,
  })
}

function redirect(doctype, docname) {
  if (!docname) return
  let name = doctype == 'Opportunity' ? 'Opportunity' : 'Lead'
  let params = { leadId: docname }
  if (name == 'Opportunity') {
    params = { opportunityId: docname }
  }
  router.push({ name: name, params: params })
}
</script>
