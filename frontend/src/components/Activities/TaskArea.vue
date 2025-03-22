<template>
  <div v-if="tasks.length">
    <div v-for="(task, i) in tasks" :key="task.name">
      <div
        class="activity flex cursor-pointer gap-6 rounded p-2.5 duration-300 ease-in-out hover:bg-surface-gray-1"
        @click="modalRef.showTask(task)"
      >
        <div class="flex flex-1 flex-col gap-1.5 text-base truncate">
          <div class="font-medium text-ink-gray-9 truncate">
            {{ task.title }}
          </div>
          <div class="flex gap-1.5 text-ink-gray-8">
            <div class="flex items-center gap-1.5">
              <UserAvatar :user="task.assigned_to" size="xs" />
              {{ getUser(task.assigned_to).full_name }}
            </div>
            <div v-if="task.due_date" class="flex items-center justify-center">
              <DotIcon class="h-2.5 w-2.5 text-ink-gray-5" :radius="2" />
            </div>
            <div v-if="task.due_date">
              <Tooltip
                :text="formatDate(task.due_date, 'ddd, MMM D, YYYY | hh:mm a')"
              >
                <div class="flex gap-2">
                  <CalendarIcon />
                  <div>{{ formatDate(task.due_date, 'D MMM, hh:mm a') }}</div>
                </div>
              </Tooltip>
            </div>
            <div class="flex items-center justify-center">
              <DotIcon class="h-2.5 w-2.5 text-ink-gray-5" :radius="2" />
            </div>
            <div class="flex gap-2">
              <TaskPriorityIcon class="!h-2 !w-2" :priority="task.priority" />
              {{ task.priority }}
            </div>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <Dropdown
            :options="taskStatusOptions(modalRef.updateTaskStatus, task)"
            @click.stop
          >
            <Tooltip :text="__('Change Status')">
              <div>
                <Button variant="ghosted" class="hover:bg-surface-gray-4">
                  <TaskStatusIcon :status="task.status" />
                </Button>
              </div>
            </Tooltip>
          </Dropdown>
          <Dropdown
            :options="[
              {
                label: __('Delete'),
                icon: 'trash-2',
                onClick: () => {
                  $dialog({
                    title: __('Delete Task'),
                    message: __('Are you sure you want to delete this task?'),
                    actions: [
                      {
                        label: __('Delete'),
                        theme: 'red',
                        variant: 'solid',
                        onClick(close) {
                          modalRef.deleteTask(task.name)
                          close()
                        },
                      },
                    ],
                  })
                },
              },
            ]"
            @click.stop
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="hover:bg-surface-gray-4 text-ink-gray-9"
            />
          </Dropdown>
        </div>
      </div>
      <div
        v-if="i < tasks.length - 1"
        class="mx-2 h-px border-t border-outline-gray-modals"
      />
    </div>
  </div>
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatDate, taskStatusOptions } from '@/utils'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { Tooltip, Dropdown } from 'frappe-ui'

const props = defineProps({
  tasks: Array,
  modalRef: Object,
})

const { getUser } = usersStore()
const { $dialog } = globalStore()
</script>
