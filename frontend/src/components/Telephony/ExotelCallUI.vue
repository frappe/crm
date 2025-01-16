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
      <span>{{ contact?.full_name ?? phoneNumber }}</span>
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
          <span>{{ counterUp?.updatedTime }}</span>
        </span>
      </div>
      <div v-else>{{ __(callStatus) }}</div>
    </div>
    <div
      v-show="showCallPopup"
      ref="callPopup"
      class="fixed z-20 w-[280px] min-h-44 flex gap-2 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 pt-2.5 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="header flex items-center justify-between gap-1 text-base">
        <div class="flex gap-2 items-center truncate">
          <div v-if="showNote || showTask" class="flex items-center gap-3">
            <Avatar
              v-if="contact?.image"
              :image="contact.image"
              :label="contact.full_name"
              class="!size-7"
            />
            <div
              v-else
              class="flex justify-center items-center size-7 rounded-full bg-surface-gray-6"
            >
              <AvatarIcon class="size-3" />
            </div>
            <div class="flex flex-col gap-1 text-base leading-4">
              <div class="font-medium">
                {{ contact.full_name ?? phoneNumber }}
              </div>
              <div class="text-ink-gray-6">
                <div v-if="callStatus == 'In progress'">
                  <span>{{ phoneNumber }}</span>
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
                    <span>{{ counterUp?.updatedTime }}</span>
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
                <span>{{ counterUp?.updatedTime }}</span>
              </span>
            </div>
            <div v-else>{{ __(callStatus) }}</div>
          </div>
        </div>

        <Button
          @click="toggleCallPopup"
          class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
          size="md"
        >
          <template #icon>
            <MinimizeIcon class="h-4 w-4 cursor-pointer" />
          </template>
        </Button>
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
          <div v-if="contact?.full_name" class="flex flex-col gap-1">
            <div class="text-lg font-medium leading-5">{{ contact.full_name }}</div>
            <div class="text-base text-ink-gray-6 leading-4">{{ phoneNumber }}</div>
          </div>
          <div v-else class="text-lg font-medium leading-5">{{ phoneNumber }}</div>
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
        <Button
          @click="closeCallPopup"
          class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
          :label="__('Close')"
          size="md"
        />
      </div>
    </div>
    <CountUpTimer ref="counterUp" />
  </div>
</template>
<script setup>
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { Avatar, Button, call } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { ref, computed, onBeforeUnmount } from 'vue'

const { getContact, getLeadContact } = contactsStore()
const { $socket } = globalStore()

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

const callStatus = ref('')
const phoneNumber = ref('')
const callData = ref(null)
const counterUp = ref(null)

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

const note = ref('')

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

const task = ref('')

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

function makeOutgoingCall(number) {
  phoneNumber.value = number
  callStatus.value = 'Calling...'
  showCallPopup.value = true
  showSmallCallPopup.value = false

  call('crm.integrations.exotel.handler.make_a_call', {
    to_number: phoneNumber.value,
  })
}

function setup() {
  $socket.on('exotel_call', (data) => {
    callData.value = data
    console.log(data)

    callStatus.value = updateStatus(data)

    if (!showCallPopup.value && !showSmallCallPopup.value) {
      showCallPopup.value = true
    }
  })
}

onBeforeUnmount(() => {
  $socket.off('exotel_call')
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
    counterUp.value.start()
    return 'In progress'
  } else if (
    data.EventType == 'terminal' &&
    data.Direction == 'outbound-api' &&
    data.Status == 'no-answer' &&
    data['Legs[1][Status]'] == 'no-answer'
  ) {
    counterUp.value.stop()
    return 'No answer'
  } else if (
    data.EventType == 'terminal' &&
    data.Direction == 'outbound-api' &&
    data.Status == 'completed'
  ) {
    counterUp.value.stop()
    return 'Call ended'
  }

  // incoming call
  if (
    data.EventType == 'Dial' &&
    data.Direction == 'incoming' &&
    data.Status == 'busy'
  ) {
    return 'Incoming call'
  } else if (
    data.EventType == 'Terminal' &&
    data.Direction == 'incoming' &&
    data.Status == 'free'
  ) {
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
</style>
