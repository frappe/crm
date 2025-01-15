<template>
  <div>
    <div
      v-show="showSmallCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-2 rounded-full bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
      @click="toggleCallPopup"
    >
      <div
        class="flex justify-center items-center size-5 rounded-full bg-surface-gray-6"
      >
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="size-3"
        />
        <AvatarIcon v-else class="size-3" />
      </div>
      <div class="text-base font-medium">
        <span
          v-if="
            callStatus == 'Calling...' ||
            callStatus == 'Ringing...' ||
            callStatus == 'Incoming Call'
          "
          class="font-normal text-ink-gray-4 mr-1"
        >
          {{ callStatus }}
        </span>
        <span>{{ phoneNumber }}</span>
        <span
          v-if="callStatus == 'In Progress'"
          class="font-normal text-ink-gray-4"
        >
          <span> · </span>00:38
        </span>
        <span
          v-else-if="callStatus == 'Call Ended' || callStatus == 'No Answer'"
          class="font-normal text-ink-gray-4"
          :class="{
            'text-red-700':
              callStatus == 'Call Ended' || callStatus == 'No Answer',
          }"
        >
          <span class="text-ink-gray-4"> · </span>
          <span>{{ callStatus }}</span>
          <span v-if="callStatus == 'Call Ended'"> <span> · </span>00:38 </span>
        </span>
      </div>
    </div>
    <Dialog
      v-model="showCallModal"
      :options="{
        title: 'Make a call',
        actions: [
          {
            label: 'Make a Call',
            variant: 'solid',
            onClick: makeCall,
          },
        ],
      }"
    >
      <template #body-content>
        <div>
          <FormControl
            v-model="phoneNumber"
            label="Phone Number"
            placeholder="+917666980887"
          />
        </div>
      </template>
    </Dialog>

    <div
      v-show="showCallPopup"
      ref="callPopup"
      class="fixed z-20 w-[280px] min-h-44 flex gap-2 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 pt-2.5 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="header flex items-center justify-between gap-2 text-base">
        <div v-if="callStatus == 'In Progress'">00:38</div>
        <div
          v-else-if="callStatus == 'Call Ended' || callStatus == 'No Answer'"
          :class="{
            'text-red-700':
              callStatus == 'Call Ended' || callStatus == 'No Answer',
          }"
        >
          <span>{{ __(callStatus) }}</span>
          <span v-if="callStatus == 'Call Ended'"><span> · </span>00:38</span>
        </div>
        <div v-else>{{ __(callStatus) }}</div>
        <div class="flex">
          <Button
            @click="toggleCallPopup"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6"
            size="md"
          >
            <template #icon>
              <MinimizeIcon class="h-4 w-4 cursor-pointer" />
            </template>
          </Button>
          <Button
            v-if="callStatus == 'Call Ended' || callStatus == 'No Answer'"
            @click="closeCallPopup"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6"
            icon="x"
            size="md"
          />
        </div>
      </div>
      <div class="body flex-1">
        <div v-if="showNote" class="h-[294px] text-base">{{ note }}</div>
        <div v-else-if="showTask" class="h-[294px] text-base">{{ task }}</div>
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
          <div v-if="contact?.full_name" class="flex flex-col gap-1.5">
            <div class="text-lg font-medium">{{ contact.full_name }}</div>
            <div class="text-base text-ink-gray-6">{{ phoneNumber }}</div>
          </div>
          <div v-else class="text-lg font-medium">{{ phoneNumber }}</div>
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
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import { Button, Dialog, FormControl, call, Avatar } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'

const { getContact, getLeadContact } = contactsStore()
const { $socket, setMakeCall } = globalStore()

const callPopup = ref(null)
const showCallPopup = ref(false)
const showSmallCallPopup = ref(false)

function toggleCallPopup() {
  showCallPopup.value = !showCallPopup.value
  if (showSmallCallPopup.value == undefined) {
    showSmallCallPopup = !showSmallCallPopup
  } else {
    showSmallCallPopup.value = !showSmallCallPopup.value
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 350, y: height.value - 250 },
  preventDefault: true,
})

const showCallModal = ref(false)
const callStatus = ref('')
const phoneNumber = ref('')
const callData = ref(null)

const contact = computed(() => {
  if (!phoneNumber.value) {
    return {
      full_name: '',
      image: '',
    }
  }
  let _contact = getContact(phoneNumber.value)
  if (!_contact) {
    _contact = getLeadContact(phoneNumber.value)
  }
  return _contact
})

const note = ref(
  'This is a note for the call. This is a note for the call. This is a note for the call. This is a note for the call.',
)

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

const task = ref('This is a task for the call. This is a task for the call.')

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

function updateWindowHeight(condition) {
  let top = parseInt(callPopup.value.style.top)
  let updatedTop = 0

  updatedTop = condition ? top - 224 : top + 224

  if (updatedTop < 0) {
    updatedTop = 10
  }

  callPopup.value.style.top = updatedTop + 'px'
}

function showMakeCallModal(number) {
  showCallModal.value = true
  phoneNumber.value = number
}

function makeCall() {
  showCallModal.value = false
  callStatus.value = 'Calling...'
  showCallPopup.value = true

  call('crm.integrations.exotel.handler.make_a_call', {
    to_number: phoneNumber.value,
  })
}

onBeforeUnmount(() => {
  $socket.off('exotel_call')
})

onMounted(() => {
  $socket.on('exotel_call', (data) => {
    callData.value = data
    console.log(data)

    callStatus.value = updateStatus(data)

    if (!showCallPopup.value && !showSmallCallPopup.value) {
      showCallPopup.value = true
    }
  })

  setMakeCall(showMakeCallModal)
})

function closeCallPopup() {
  showCallPopup.value = false
  showSmallCallPopup.value = false
  note.value = ''
  task.value = ''
}

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
    return 'In Progress'
  } else if (
    data.EventType == 'terminal' &&
    data.Direction == 'outbound-api' &&
    (data.Status == 'completed' || data.Status == 'no-answer')
  ) {
    return data.Status == 'no-answer' ? 'No Answer' : 'Call Ended'
  }

  // incoming call
  if (
    data.EventType == 'Dial' &&
    data.Direction == 'incoming' &&
    data.Status == 'busy'
  ) {
    return 'Incoming Call'
  } else if (
    data.EventType == 'Terminal' &&
    data.Direction == 'incoming' &&
    data.Status == 'free'
  ) {
    return 'Call Ended'
  }
}
</script>
