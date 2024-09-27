<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => updateTask(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-gray-900">
          {{ editMode ? __('Edit Task') : __('Create Task') }}
        </h3>
        <Button
          v-if="task?.reference_docname"
          variant="outline"
          size="sm"
          :label="
            task.reference_doctype == 'CRM Deal'
              ? __('Open Deal')
              : __('Open Lead')
          "
          @click="redirect()"
        >
          <template #suffix>
            <ArrowUpRightIcon class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ __('Title') }}</div>
          <TextInput
            ref="title"
            variant="outline"
            v-model="_task.title"
            :placeholder="__('Call with John Doe')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">
            {{ __('Description') }}
          </div>
          <TextEditor
            variant="outline"
            ref="description"
            editor-class="!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubbleMenu="true"
            :content="_task.description"
            @change="(val) => (_task.description = val)"
            :placeholder="
              __('Took a call with John Doe and discussed the new project.')
            "
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
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
            :placeholder="__('John Doe')"
            :hideMe="true"
          >
            <template #prefix>
              <UserAvatar class="mr-2 !h-4 !w-4" :user="_task.assigned_to" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                <div class="cursor-pointer">
                  {{ getUser(option.value).full_name }}
                </div>
              </Tooltip>
            </template>
          </Link>
          <DateTimePicker
            class="datepicker w-36"
            v-model="_task.due_date"
            :placeholder="__('01/04/2024 11:30 PM')"
            input-class="border-none"
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
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { taskStatusOptions, taskPriorityOptions } from '@/utils'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { TextEditor, Dropdown, Tooltip, call, DateTimePicker } from 'frappe-ui'
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

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

const emit = defineEmits(['updateTask', 'after'])

const router = useRouter()
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
  reference_doctype: props.doctype,
  reference_docname: null,
})

function updateTaskStatus(status) {
  _task.value.status = status
}

function updateTaskPriority(priority) {
  _task.value.priority = priority
}

function redirect() {
  if (!props.task?.reference_docname) return
  let name = props.task.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: props.task.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.task.reference_docname }
  }
  router.push({ name: name, params: params })
}

async function updateTask() {
  if (!_task.value.assigned_to) {
    _task.value.assigned_to = getUser().name
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
      capture('task_created')
      tasks.value.reload()
      emit('after')
    }
  }
  show.value = false
}

function render() {
  editMode.value = false
  nextTick(() => {
    title.value?.el?.focus?.()
    _task.value = { ...props.task }
    if (_task.value.title) {
      editMode.value = true
    }
  })
}

onMounted(() => show.value && render())

watch(show, (value) => {
  if (!value) return
  render()
})
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
