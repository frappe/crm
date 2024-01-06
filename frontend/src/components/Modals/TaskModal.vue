<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode ? 'Edit Task' : 'Create Task',
      size: 'xl',
      actions: [
        {
          label: editMode ? 'Update' : 'Create',
          variant: 'solid',
          onClick: () => updateTask(),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Title</div>
          <TextInput
            ref="title"
            variant="outline"
            v-model="_task.title"
            placeholder="Add Title"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">Description</div>
          <TextEditor
            variant="outline"
            ref="description"
            editor-class="!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubbleMenu="true"
            :content="_task.description"
            @change="(val) => (_task.description = val)"
            placeholder="Type a Description"
          />
        </div>
        <div class="flex items-center gap-2">
          <Dropdown :options="taskStatusOptions(updateTaskStatus)">
            <Button :label="_task.status" class="w-full justify-between">
              <template #prefix>
                <TaskStatusIcon :status="_task.status" />
              </template>
            </Button>
          </Dropdown>
          <Link
            class="form-control"
            :value="getUser(_task.assigned_to).full_name"
            doctype="User"
            @change="(option) => (_task.assigned_to = option)"
            placeholder="Assignee"
          >
            <template #prefix>
              <UserAvatar class="mr-2 !h-4 !w-4" :user="_task.assigned_to" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                {{ getUser(option.value).full_name }}
              </Tooltip>
            </template>
          </Link>
          <DatePicker
            class="datepicker w-36"
            v-model="_task.due_date"
            placeholder="Due Date"
            input-class="border-none"
            :formatValue="(val) => val.split('-').reverse().join('-')"
          />
          <Dropdown :options="taskPriorityOptions(updateTaskPriority)">
            <Button :label="_task.priority" class="w-full justify-between">
              <template #prefix>
                <TaskPriorityIcon :priority="_task.priority" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { taskStatusOptions, taskPriorityOptions } from '@/utils'
import { usersStore } from '@/stores/users'
import { TextEditor, Dropdown, Tooltip, DatePicker, call } from 'frappe-ui'
import { ref, defineModel, watch, nextTick } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const tasks = defineModel('reloadTasks')

const emit = defineEmits(['updateTask'])

const { getUser } = usersStore()

const title = ref(null)
const editMode = ref(false)
const _task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
})

function updateTaskStatus(status) {
  _task.value.status = status
}

function updateTaskPriority(priority) {
  _task.value.priority = priority
}

async function updateTask() {
  if (!_task.value.assigned_to) {
    _task.value.assigned_to = getUser().email
  }
  if (_task.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: _task.value.name,
      fieldname: _task.value,
    })
    if (d.name) {
      tasks.value.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Task',
        reference_doctype: props.doctype,
        reference_docname: props.doc || null,
        ..._task.value,
      },
    })
    if (d.name) {
      tasks.value.reload()
    }
  }
  show.value = false
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      title.value.el.focus()
      _task.value = { ...props.task }
      if (_task.value.title) {
        editMode.value = true
      }
    })
  }
)
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
