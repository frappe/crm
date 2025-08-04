<template>
  <div>
    <div
      v-show="showSmallCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-1 rounded-full bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
      @click="toggleCallPopup"
    >
      <div
        class="flex justify-center items-center size-5 rounded-full bg-surface-gray-6 shrink-0 mr-1"
      >
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="!size-5"
        />
        <AvatarIcon v-else class="size-3" />
      </div>
      <span>{{ contact?.full_name ?? contact?.mobile_no }}</span>
      <span>·</span>
      <div v-if="callStatus == 'In progress'">
        {{ counterUp?.updatedTime }}
      </div>
      <div
        v-else-if="callStatus == 'Call ended' || callStatus == 'No answer'"
        class="blink"
        :class="{
          'text-red-700':
            callStatus == 'Call ended' || callStatus == 'No answer',
        }"
      >
        <span>{{ __(callStatus) }}</span>
        <span v-if="callStatus == 'Call ended'">
          <span> · </span>
          <span>{{ callDuration }}</span>
        </span>
      </div>
      <div v-else>{{ __(callStatus) }}</div>
    </div>
    <div
      v-show="showCallPopup"
      class="fixed z-20 w-[280px] min-h-44 flex gap-2 flex-col rounded-lg bg-surface-gray-7 p-4 pt-2.5 text-ink-gray-2 shadow-2xl"
      :style="style"
      @click.stop
    >
      <div
        ref="callPopupHeader"
        class="header flex items-center justify-between gap-1 text-base cursor-move select-none"
      >
        <div class="flex gap-2 items-center truncate">
          <div
            v-if="showNote || showTask"
            class="flex items-center gap-3 truncate"
          >
            <Avatar
              v-if="contact?.image"
              :image="contact.image"
              :label="contact.full_name"
              class="!size-7 shrink-0"
            />
            <div
              v-else
              class="flex justify-center items-center size-7 rounded-full bg-surface-gray-6 shrink-0"
            >
              <AvatarIcon class="size-3" />
            </div>
            <div
              class="flex flex-col gap-1 text-base leading-4 overflow-hidden"
            >
              <div class="font-medium truncate">
                {{ contact?.full_name ?? contact?.mobile_no }}
              </div>
              <div class="text-ink-gray-6">
                <div v-if="callStatus == 'In progress'">
                  <span>{{ contact?.mobile_no }}</span>
                  <span> · </span>
                  <span>{{ counterUp?.updatedTime }}</span>
                </div>
                <div
                  v-else-if="
                    callStatus == 'Call ended' || callStatus == 'No answer'
                  "
                  class="blink"
                  :class="{
                    'text-red-700':
                      callStatus == 'Call ended' || callStatus == 'No answer',
                  }"
                >
                  <span>{{ __(callStatus) }}</span>
                  <span v-if="callStatus == 'Call ended'">
                    <span> · </span>
                    <span>{{ callDuration }}</span>
                  </span>
                </div>
                <div v-else>{{ __(callStatus) }}</div>
              </div>
            </div>
          </div>
          <div v-else>
            <div v-if="callStatus == 'In progress'">
              {{ counterUp?.updatedTime }}
            </div>
            <div
              v-else-if="
                callStatus == 'Call ended' || callStatus == 'No answer'
              "
              class="blink"
              :class="{
                'text-red-700':
                  callStatus == 'Call ended' || callStatus == 'No answer',
              }"
            >
              <span>{{ __(callStatus) }}</span>
              <span v-if="callStatus == 'Call ended'">
                <span> · </span>
                <span>{{ callDuration }}</span>
              </span>
            </div>
            <div v-else>{{ __(callStatus) }}</div>
          </div>
        </div>

        <div class="flex">
          <Button
            @click="toggleCallPopup"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
            size="md"
          >
            <template #icon>
              <MinimizeIcon class="h-4 w-4 cursor-pointer" />
            </template>
          </Button>
          <Button
            v-if="callStatus == 'Call ended' || callStatus == 'No answer'"
            @click="closeCallPopup"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
            icon="x"
            size="md"
          />
        </div>
      </div>
      <div class="body flex-1">
        <div v-if="showNote">
          <TextEditor
            variant="ghost"
            ref="content"
            editor-class="prose-sm h-[290px] text-ink-white overflow-auto mt-1"
            :bubbleMenu="true"
            :content="note.content"
            @change="(val) => (note.content = val)"
            :placeholder="__('Take a note...')"
          />
        </div>
        <TaskPanel ref="taskRef" v-else-if="showTask" :task="task" />
        <div v-else class="flex items-center gap-3">
          <Avatar
            v-if="contact?.image"
            :image="contact.image"
            :label="contact.full_name"
            class="!size-8"
          />
          <div
            v-else
            class="flex justify-center items-center size-8 rounded-full bg-surface-gray-6"
          >
            <AvatarIcon class="size-4" />
          </div>
          <div v-if="contact?.full_name" class="flex flex-col gap-1">
            <div class="text-lg font-medium leading-5">
              {{ contact.full_name }}
            </div>
            <div class="text-base text-ink-gray-6 leading-4">
              {{ contact.mobile_no }}
            </div>
          </div>
          <div v-else class="text-lg font-medium leading-5">
            {{ contact.mobile_no }}
          </div>
        </div>
      </div>
      <div class="footer flex justify-between gap-2">
        <div class="flex gap-2">
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
            @click="showNoteWindow"
          >
            <template #icon>
              <NoteIcon class="w-4 h-4" />
            </template>
          </Button>
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
            @click="showTaskWindow"
          >
            <template #icon>
              <TaskIcon class="w-4 h-4" />
            </template>
          </Button>
          <Button
            v-if="contact.deal || contact.lead"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
            :label="contact.deal ? __('Deal') : __('Lead')"
            @click="openDealOrLead"
          >
            <template #suffix>
              <ArrowUpRightIcon class="w-4 h-4" />
            </template>
          </Button>
        </div>

        <Button
          v-if="(note.name || task.name) && dirty"
          @click="update"
          class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
          variant="solid"
          :label="__('Update')"
          size="md"
        />
        <Button
          v-else-if="
            ((note?.content && note.content != '<p></p>') || task.title) &&
            !note.name &&
            !task.name
          "
          @click="save"
          class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
          variant="solid"
          :label="__('Save')"
          size="md"
        />
      </div>
    </div>
    <CountUpTimer ref="counterUp" />
  </div>
</template>
<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import TaskPanel from '@/components/Telephony/TaskPanel.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { globalStore } from '@/stores/global'
import { sessionStore } from '@/stores/session'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { TextEditor, Avatar, Button, createResource, toast } from 'frappe-ui'
import { ref, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const { $socket } = globalStore()

const callPopupHeader = ref(null)
const showCallPopup = ref(false)
let showSmallCallPopup = ref(false)

function toggleCallPopup() {
  showCallPopup.value = !showCallPopup.value
  if (showSmallCallPopup.value == undefined) {
    showSmallCallPopup = !showSmallCallPopup
  } else {
    showSmallCallPopup.value = !showSmallCallPopup.value
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 250 },
  preventDefault: true,
})

const callStatus = ref('')
const phoneNumber = ref('')
const callData = ref(null)
const counterUp = ref(null)

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  onSuccess(data) {
    contact.value = data
  },
})

watch(
  phoneNumber,
  (value) => {
    if (!value) return
    getContact.fetch()
  },
  { immediate: true },
)

const dirty = ref(false)

const note = ref({
  name: '',
  content: '',
})

const showNote = ref(false)

function showNoteWindow() {
  showNote.value = !showNote.value
  if (!showTask.value) {
    updateWindowHeight(showNote.value)
  }
  if (showNote.value) {
    showTask.value = false
  }
}

function createUpdateNote() {
  createResource({
    url: 'crm.integrations.api.add_note_to_call_log',
    params: {
      call_sid: callData.value.CallSid,
      note: note.value,
    },
    auto: true,
    onSuccess(_note) {
      note.value['name'] = _note.name
      nextTick(() => {
        dirty.value = false
      })
    },
  })
}

const task = ref({
  name: '',
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
})

const showTask = ref(false)

function showTaskWindow() {
  showTask.value = !showTask.value
  if (!showNote.value) {
    updateWindowHeight(showTask.value)
  }
  if (showTask.value) {
    showNote.value = false
  }
}

function createUpdateTask() {
  createResource({
    url: 'crm.integrations.api.add_task_to_call_log',
    params: {
      call_sid: callData.value.CallSid,
      task: task.value,
    },
    auto: true,
    onSuccess(_task) {
      task.value['name'] = _task.name
      nextTick(() => {
        dirty.value = false
      })
    },
  })
}

watch([note, task], () => (dirty.value = true), { deep: true })

function updateWindowHeight(condition) {
  let callPopup = callPopupHeader.value.parentElement
  let top = parseInt(callPopup.style.top)
  let updatedTop = 0

  updatedTop = condition ? top - 224 : top + 224

  if (updatedTop < 0) {
    updatedTop = 10
  }

  callPopup.style.top = updatedTop + 'px'
}

function makeOutgoingCall(number) {
  phoneNumber.value = number

  createResource({
    url: 'crm.integrations.exotel.handler.make_a_call',
    params: { to_number: phoneNumber.value },
    auto: true,
    onSuccess(callDetails) {
      callData.value = callDetails
      console.log(callDetails)

      callStatus.value = 'Calling...'
      showCallPopup.value = true
      showSmallCallPopup.value = false
    },
    onError(err) {
      toast.error(err.messages[0])
    },
  })
}

function setup() {
  $socket.on('exotel_call', (data) => {
    callData.value = data
    console.log(data)

    callStatus.value = updateStatus(data)
    const { user } = sessionStore()

    if (!showCallPopup.value && !showSmallCallPopup.value) {
      if (data.AgentEmail && data.AgentEmail == (user || user.value)) {
        // Incoming call
        phoneNumber.value = data.CallFrom || data.From
        showCallPopup.value = true
      } else {
        // Outgoing call
        phoneNumber.value = data.To
      }
    }
  })
}

onBeforeUnmount(() => {
  $socket.off('exotel_call')
})

const router = useRouter()

function openDealOrLead() {
  if (contact.value.deal) {
    router.push({
      name: 'Deal',
      params: { dealId: contact.value.deal },
    })
  } else if (contact.value.lead) {
    router.push({
      name: 'Lead',
      params: { leadId: contact.value.lead },
    })
  }
}

function closeCallPopup() {
  showCallPopup.value = false
  showSmallCallPopup.value = false
  note.value = {
    name: '',
    content: '',
  }
  task.value = {
    name: '',
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    status: 'Backlog',
    priority: 'Low',
  }
}

function save() {
  if (note.value.content) createUpdateNote()
  if (task.value.title) createUpdateTask()
}

function update() {
  if (note.value.content) createUpdateNote()
  if (task.value.title) createUpdateTask()
}

const callDuration = ref('00:00')

function updateStatus(data) {
  // outgoing call
  if (
    data.EventType == 'answered' &&
    data.Direction == 'outbound-api' &&
    data.Status == 'in-progress' &&
    data['Legs[0][Status]'] == 'in-progress' &&
    data['Legs[1][Status]'] == ''
  ) {
    return 'Ringing...'
  } else if (
    data.EventType == 'answered' &&
    data.Direction == 'outbound-api' &&
    data.Status == 'in-progress' &&
    data['Legs[1][Status]'] == 'in-progress'
  ) {
    counterUp.value.start()
    return 'In progress'
  } else if (
    data.EventType == 'terminal' &&
    data.Direction == 'outbound-api' &&
    (data.Status == 'no-answer' || data.Status == 'busy') &&
    (data['Legs[1][Status]'] == 'no-answer' ||
      data['Legs[0][Status]'] == 'no-answer' ||
      data['Legs[1][Status]'] == 'busy' ||
      data['Legs[0][Status]'] == 'busy')
  ) {
    counterUp.value.stop()
    return 'No answer'
  } else if (
    data.EventType == 'terminal' &&
    data.Direction == 'outbound-api' &&
    data.Status == 'completed'
  ) {
    counterUp.value.stop()
    callDuration.value = counterUp.value.getTime(
      parseInt(data['Legs[0][OnCallDuration]']) ||
        parseInt(data.DialCallDuration),
    )
    return 'Call ended'
  }

  // incoming call
  if (
    data.EventType == 'Dial' &&
    data.Direction == 'incoming' &&
    data.Status == 'busy'
  ) {
    phoneNumber.value = data.From || data.CallFrom
    return 'Incoming call'
  } else if (
    data.Direction == 'incoming' &&
    data.CallType == 'incomplete' &&
    data.DialCallStatus == 'no-answer'
  ) {
    return 'No answer'
  } else if (
    data.Direction == 'incoming' &&
    (data.CallType == 'completed' || data.CallType == 'client-hangup') &&
    (data.DialCallStatus == 'completed' || data.DialCallStatus == 'canceled')
  ) {
    callDuration.value = counterUp.value.getTime(
      parseInt(data['Legs[0][OnCallDuration]']) ||
        parseInt(data.DialCallDuration),
    )
    return 'Call ended'
  }
}

defineExpose({ makeOutgoingCall, setup })
</script>
<style scoped>
@keyframes blink {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

.blink {
  animation: blink 1s ease-in-out 6;
}

:deep(.ProseMirror) {
  caret-color: var(--ink-white);
}
</style>
