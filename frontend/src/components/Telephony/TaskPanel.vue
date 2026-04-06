<template>
  <div class="h-[294px] text-base">
    <FormControl
      v-model="task.title"
      type="text"
      variant="ghost"
      class="mb-2 title"
      :placeholder="__('Schedule a task...')"
    />
    <TextEditor
      ref="content"
      variant="ghost"
      editor-class="prose-sm h-[150px] text-ink-white overflow-auto"
      :bubbleMenu="true"
      :content="task.description"
      :placeholder="__('Add description...')"
      @change="(val) => (task.description = val)"
    />
    <div class="flex flex-col gap-2">
      <div class="flex gap-2">
        <Dropdown :options="taskStatusOptions(updateTaskStatus)">
          <Button
            :label="task.status"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
          >
            <template #prefix>
              <TaskStatusIcon :status="task.status" />
            </template>
          </Button>
        </Dropdown>
        <Dropdown :options="taskPriorityOptions(updateTaskPriority)">
          <Button
            :label="task.priority"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
          >
            <template #prefix>
              <TaskPriorityIcon :priority="task.priority" />
            </template>
          </Button>
        </Dropdown>
      </div>
      <Link
        class="user"
        :value="getUser(task.assigned_to).full_name"
        doctype="User"
        :placeholder="__('John Doe')"
        :filters="{
          name: ['in', users.data?.crmUsers?.map((user) => user.name)],
          ignore_user_type: 1,
        }"
        :hideMe="true"
        @change="(option) => (task.assigned_to = option)"
      >
        <template #prefix>
          <UserAvatar class="mr-2 !h-4 !w-4" :user="task.assigned_to" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            <div class="cursor-pointer text-ink-gray-9">
              {{ getUser(option.value).full_name }}
            </div>
          </Tooltip>
        </template>
      </Link>
      <DateTimePicker
        v-model="task.due_date"
        class="datepicker w-36"
        :placeholder="__('01/04/2024 11:30 PM')"
        :formatter="(date) => getFormat(date, '', true, true)"
        input-class="border-none"
      />
    </div>
  </div>
</template>
<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { taskStatusOptions, taskPriorityOptions, getFormat } from '@/utils'
import { TextEditor, Dropdown, Tooltip, DateTimePicker } from 'frappe-ui'
import { reactive } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    default: () => ({
      title: '',
      description: '',
      assigned_to: '',
      due_date: '',
      status: 'Backlog',
      priority: 'Low',
    }),
  },
})

const task = reactive(props.task)

const { users, getUser } = usersStore()

function updateTaskStatus(status) {
  task.status = status
}

function updateTaskPriority(priority) {
  task.priority = priority
}
</script>
<style scoped>
:deep(.title input) {
  background-color: var(--surface-gray-7);
  caret-color: var(--ink-white);
  color: var(--ink-white);
  outline: none;
  border: none;
  padding: 0;
}
:deep(.datepicker input) {
  background-color: var(--surface-gray-6);
  caret-color: var(--ink-white);
  color: var(--ink-white);
  outline: none;
  border: none;
}

:deep(.title input:focus),
:deep(.datepicker input:focus) {
  border: none;
  outline: none;
  box-shadow: none;
}

:deep(.user button) {
  background-color: var(--surface-gray-6);
  border: none;
  color: var(--ink-white);
}
:deep(.user button:hover) {
  background-color: var(--surface-gray-5);
  border: none;
}
:deep(.user button:focus) {
  box-shadow: none;
  outline: none;
}
</style>
