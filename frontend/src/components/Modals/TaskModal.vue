<template>
  <Dialog
    v-model="dialogShow"
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
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Task') : __('Create Task') }}
        </h3>
        <Button
          v-if="task?.reference_docname"
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
          <FormControl
            ref="title"
            :label="__('Title')"
            v-model="_task.title"
            :placeholder="__('Call with John Doe')"
            @update:modelValue="handleFieldChange"
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">
            {{ __('Description') }}
          </div>
          <TextEditor
            variant="outline"
            ref="description"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_task.description"
            @change="(val) => { _task.description = val; handleFieldChange(); }"
            :placeholder="
              __('Took a call with John Doe and discussed the new project.')
            "
          />
        </div>
        <div class="flex flex-nowrap items-center gap-2">
          <Dropdown :options="taskStatusOptions(updateTaskStatus)">
            <Button :label="extractLabel(_task.status, translateTaskStatus)" class="w-full justify-between whitespace-nowrap">
              <template #prefix>
                <TaskStatusIcon :status="extractValue(_task.status)" />
              </template>
            </Button>
          </Dropdown>
          <Link
            class="form-control flex-1"
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
                <div class="cursor-pointer text-ink-gray-9">
                  {{ getUser(option.value).full_name }}
                </div>
              </Tooltip>
            </template>
          </Link>
          <input
            type="datetime-local"
            v-model="_task.due_date"
            class="flex-1"
            @click.stop
            @update:modelValue="handleFieldChange"
          />
          <Dropdown :options="taskPriorityOptions(updateTaskPriority)">
            <Button :label="extractLabel(_task.priority, translateTaskPriority)" class="w-full justify-between">
              <template #prefix>
                <TaskPriorityIcon :priority="extractValue(_task.priority)" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </div>
    </template>
  </Dialog>
  <ConfirmCloseDialog 
    v-model="showConfirmClose"
    @confirm="confirmClose"
    @cancel="cancelClose"
  />
</template>

<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { taskStatusOptions, taskPriorityOptions, extractValue, extractLabel } from '@/utils'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { TextEditor, Dropdown, Tooltip, call } from 'frappe-ui'
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { translateTaskStatus } from '@/utils/taskStatusTranslations'
import { translateTaskPriority } from '@/utils/taskPriorityTranslations'
import ConfirmCloseDialog from '@/components/Modals/ConfirmCloseDialog.vue'

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
const dialogShow = ref(false)
const showConfirmClose = ref(false)
const tasks = defineModel('reloadTasks')

const emit = defineEmits(['updateTask', 'after'])

const router = useRouter()
const { getUser } = usersStore()

const title = ref(null)
const editMode = ref(false)
const isDirty = ref(false)
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
  _task.value.status = extractValue(status)
}

function updateTaskPriority(priority) {
  _task.value.priority = extractValue(priority)
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
  const taskData = {
    ..._task.value,
    status: extractValue(_task.value.status),
    priority: extractValue(_task.value.priority)
  }
  if (_task.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: _task.value.name,
      fieldname: taskData,
    })
    if (d.name) {
      tasks.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Task',
        reference_doctype: props.doctype,
        reference_docname: props.doc || null,
        ...taskData,
      },
    })
    if (d.name) {
      capture('task_created')
      tasks.value?.reload()
      emit('after', d, true)
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

watch(
  () => show.value,
  (value) => {
    if (value === dialogShow.value) return
    if (value) {
      render()
      isDirty.value = false
      dialogShow.value = true
    }
  },
  { immediate: true }
)

watch(
  () => dialogShow.value,
  (value) => {
    if (value) return
    if (isDirty.value) {
      showConfirmClose.value = true
      nextTick(() => {
        dialogShow.value = true
      })
    } else {
      show.value = false
    }
  }
)

function handleFieldChange() {
  isDirty.value = true
}

function handleClose() {
  if (isDirty.value) {
    showConfirmClose.value = true
  } else {
    dialogShow.value = false
    show.value = false
  }
}

function confirmClose() {
  isDirty.value = false
  dialogShow.value = false
  show.value = false
}

function cancelClose() {
  showConfirmClose.value = false
}
</script>
