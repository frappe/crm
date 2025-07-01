<template>
  <Dialog v-model="show">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Call Details') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Dropdown
              :options="[
                {
                  group: __('Options'),
                  hideLabel: true,
                  items: [
                    {
                      label: note?.name ? __('Edit note') : __('Add note'),
                      icon: NoteIcon,
                      onClick: addEditNote,
                    },
                    {
                      label: task?.name ? __('Edit task') : __('Add task'),
                      icon: TaskIcon,
                      onClick: addEditTask,
                    },
                  ],
                },
              ]"
            >
              <template #default>
                <Button variant="ghost" icon="more-horizontal" />
              </template>
            </Dropdown>
            <Button
              v-if="!isMobileView"
              variant="ghost"
              class="w-7"
              @click="openCallLogModal"
            >
              <template #icon>
                <EditIcon />
              </template>
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
          </div>
        </div>
        <div class="flex flex-col gap-3.5">
          <div
            v-for="field in detailFields"
            :key="field.name"
            class="flex gap-2 text-base text-ink-gray-8"
          >
            <div class="grid size-7 place-content-center">
              <component :is="field.icon" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <div
                v-if="field.name == 'receiver'"
                class="flex items-center gap-1"
              >
                <Avatar
                  :image="field.value.caller.image"
                  :label="field.value.caller.label"
                  size="sm"
                />
                <div class="ml-1 flex flex-col gap-1">
                  {{ field.value.caller.label }}
                </div>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-ink-gray-5"
                />
                <Avatar
                  :image="field.value.receiver.image"
                  :label="field.value.receiver.label"
                  size="sm"
                />
                <div class="ml-1 flex flex-col gap-1">
                  {{ field.value.receiver.label }}
                </div>
              </div>
              <Tooltip v-else-if="field.tooltip" :text="field.tooltip">
                {{ field.value }}
              </Tooltip>
              <div class="w-full" v-else-if="field.name == 'recording_url'">
                <audio
                  class="audio-control w-full"
                  controls
                  :src="field.value"
                ></audio>
              </div>
              <div
                class="w-full cursor-pointer rounded border px-2 pt-1.5 text-base text-ink-gray-7"
                v-else-if="field.name == 'note'"
                @click="() => (showNoteModal = true)"
              >
                <FadedScrollableDiv class="max-h-24 min-h-16 overflow-y-auto">
                  <div
                    v-if="field.value?.title"
                    :class="[field.value?.content ? 'mb-1 font-bold' : '']"
                    v-html="field.value?.title"
                  />
                  <div
                    v-if="field.value?.content"
                    v-html="field.value?.content"
                  />
                </FadedScrollableDiv>
              </div>
              <div
                class="w-full cursor-pointer rounded border px-2 pt-1.5 text-base text-ink-gray-7"
                v-else-if="field.name == 'task'"
                @click="() => (showTaskModal = true)"
              >
                <FadedScrollableDiv class="max-h-24 min-h-16 overflow-y-auto">
                  <div
                    v-if="field.value?.title"
                    :class="[field.value?.description ? 'mb-1 font-bold' : '']"
                    v-html="field.value?.title"
                  />
                  <div
                    v-if="field.value?.description"
                    v-html="field.value?.description"
                  />
                </FadedScrollableDiv>
              </div>
              <div v-else :class="field.color ? `text-${field.color}-600` : ''">
                {{ field.value }}
              </div>
              <div v-if="field.link">
                <ArrowUpRightIcon
                  class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                  @click="() => field.link()"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="!callLog?.data?._lead && !callLog?.data?._deal"
        class="px-4 pb-7 pt-4 sm:px-6"
      >
        <Button
          class="w-full"
          variant="solid"
          :label="__('Create lead')"
          @click="createLead"
        />
      </div>
    </template>
  </Dialog>
  <NoteModal v-model="showNoteModal" :note="note" @after="addNoteToCallLog" />
  <TaskModal v-model="showTaskModal" :task="task" @after="addTaskToCallLog" />
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import Dealsicon from '@/components/Icons/DealsIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CheckCircleIcon from '@/components/Icons/CheckCircleIcon.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import { getCallLogDetail } from '@/utils/callLog'
import { isMobileView } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { FeatherIcon, Dropdown, Avatar, Tooltip, call } from 'frappe-ui'
import { ref, computed, h, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const show = defineModel()
const showNoteModal = ref(false)
const showTaskModal = ref(false)

const callLog = defineModel('callLog')

const note = ref({
  title: '',
  content: '',
})

const task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
})

const detailFields = computed(() => {
  if (!callLog.value?.data) return []

  let data = JSON.parse(JSON.stringify(callLog.value?.data))

  for (const key in data) {
    data[key] = getCallLogDetail(key, data)
  }

  note.value = data._notes?.[0] ?? null
  task.value = data._tasks?.[0] ?? null

  let details = [
    {
      icon: h(FeatherIcon, {
        name: data.type.icon,
        class: 'h-3.5 w-3.5',
      }),
      name: 'type',
      value: data.type.label + ' Call',
    },
    {
      icon: ContactsIcon,
      name: 'receiver',
      value: {
        receiver: data.receiver,
        caller: data.caller,
      },
    },
    {
      icon: data._lead ? LeadsIcon : Dealsicon,
      name: 'reference_doc',
      value: data._lead ? 'Lead' : 'Deal',
      link: () => {
        if (data._lead) {
          router.push({
            name: 'Lead',
            params: { leadId: data._lead },
          })
        } else {
          router.push({
            name: 'Deal',
            params: { dealId: data._deal },
          })
        }
      },
      condition: () => data._lead || data._deal,
    },
    {
      icon: CalendarIcon,
      name: 'creation',
      value: data.creation.label,
      tooltip: data.creation.label,
    },
    {
      icon: DurationIcon,
      name: 'duration',
      value: data.duration.label,
    },
    {
      icon: CheckCircleIcon,
      name: 'status',
      value: data.status.label,
      color: data.status.color,
    },
    {
      icon: h(FeatherIcon, {
        name: 'play-circle',
        class: 'h-4 w-4 mt-2',
      }),
      name: 'recording_url',
      value: data.recording_url,
    },
    {
      icon: NoteIcon,
      name: 'note',
      value: data._notes?.[0] ?? null,
    },
    {
      icon: TaskIcon,
      name: 'task',
      value: data._tasks?.[0] ?? null,
    },
  ]

  return details
    .filter((detail) => detail.value)
    .filter((detail) => (detail.condition ? detail.condition() : true))
})

const d = ref({})
const leadDetails = ref({})

async function createLead() {
  await d.value.triggerOnCreateLead?.(
    callLog.value?.data,
    leadDetails.value,
    () => (show.value = false),
  )

  call('crm.fcrm.doctype.crm_call_log.crm_call_log.create_lead_from_call_log', {
    call_log: callLog.value?.data,
    lead_details: leadDetails.value,
  }).then((d) => {
    if (d) {
      router.push({ name: 'Lead', params: { leadId: d } })
    }
  })
}

const showCallLogModal = defineModel('callLogModal')

function openCallLogModal() {
  showCallLogModal.value = true
  nextTick(() => {
    show.value = false
  })
}

function addEditNote() {
  if (!note.value?.name) {
    note.value = {
      title: '',
      content: '',
    }
  }
  showNoteModal.value = true
}

function addEditTask() {
  if (!task.value?.name) {
    task.value = {
      title: '',
      description: '',
      assigned_to: '',
      due_date: '',
      status: 'Backlog',
      priority: 'Low',
    }
  }
  showTaskModal.value = true
}

async function addNoteToCallLog(_note, insert_mode = false) {
  note.value = _note
  if (insert_mode && _note.name) {
    await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: callLog.value?.data?.id,
      note: _note,
    })
  }
}

async function addTaskToCallLog(_task, insert_mode = false) {
  task.value = _task
  if (insert_mode && _task.name) {
    await call('crm.integrations.api.add_task_to_call_log', {
      call_sid: callLog.value?.data?.id,
      task: _task,
    })
  }
}

watch(
  () => callLog.value?.data?.name,
  (value) => {
    if (!value) return
    d.value = useDocument('CRM Call Log', value)
  },
)
</script>

<style scoped>
.audio-control {
  height: 36px;
  outline: none;
  border-radius: 10px;
  cursor: pointer;
  background-color: rgb(237, 237, 237);
}

audio::-webkit-media-controls-panel {
  background-color: rgb(237, 237, 237) !important;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
