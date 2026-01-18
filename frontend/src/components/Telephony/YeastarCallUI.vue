<template>
  <div v-show="showCallPopup" :style="style" @click.stop class="fixed z-20">
    <div
      class="w-[300px] rounded-2xl bg-gray-900 shadow-2xl p-4 text-white border border-gray-800"
    >
      <div v-show="!showNote">
        <div
          ref="callPopupHeader"
          class="flex items-center gap-3 mb-4 cursor-move active:cursor-grabbing select-none"
        >
          <div
            class="h-9 w-9 flex items-center justify-center rounded-full bg-blue-600/20"
          >
            <PhoneIcon class="h-4 w-4 text-blue-500 animate-pulse" />
          </div>

          <div class="flex flex-col">
            <span class="text-sm text-gray-400">Call Status</span>
            <span class="font-semibold text-lg leading-tight">
              {{ callStatus || 'Ready' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-4 mb-4">
          <Avatar shape="circle" label="U" size="lg" />

          <div class="flex flex-col">
            <span class="font-medium text-white"></span>
            <small>Yeastar</small>
            <div>
              <span class="text-sm text-gray-400">
                ({{ contactDetails.number }})
              </span>
              <small>{{ stateMap(callStatusChangeState.status) }}....</small>
            </div>
          </div>
        </div>

        <div
          v-if="initiateCallResource.data && isOutgoing"
          class="mt-3 rounded-lg bg-gray-800/60 px-3 py-2 text-sm text-gray-300"
        >
          <span class="text-green-400 font-medium">
            Connection successful
          </span>
          <div class="text-xs mt-1 text-gray-400">
            Pick up your Yeastar IP phone to start the call
          </div>
        </div>
      </div>

      <div class="mt-4 border-t border-gray-800 pt-3">
        <div
          class="flex items-center justify-between group cursor-pointer mb-2"
          @click="showNoteWindow"
        >
          <span
            class="text-xs font-medium uppercase tracking-wider text-gray-500"
            >Call Notes</span
          >
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            :tooltip="showNote ? 'Hide Note' : 'Show Note'"
            :icon="showNote ? 'chevron-up' : NoteIcon"
            size="sm"
          />
        </div>

        <div
          v-if="showNote"
          class="space-y-3 transition-all duration-300 ease-in-out"
        >
          <div class="text-white bg-surface-gray-6 -800 rounded-md p-2">
            <TextEditor
              variant="ghost"
              ref="content"
              editor-class="prose-sm h-[200px] text-ink-white overflow-auto "
              :bubbleMenu="true"
              :content="note.content"
              @change="(val) => (note.content = val)"
              :placeholder="'Take a note...'"
            />
          </div>

          <div class="flex items-center justify-end gap-2">
            <Button
              variant="ghost"
              theme=""
              class="text-gray-400"
              size="sm"
              label="Clear"
              @click="note.content = ''"
              v-if="note.content"
            />
            <Button
              class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
              variant="solid"
              :label="__('Save')"
              size="md"
              :disabled="!note.content"
              @click="createUpdateNote"
            />
          </div>
        </div>
      </div>

      <div
        v-show="isIncoming && !agentAnswered"
        class="flex flex-row p-2 mt-4 justify-between gap-2"
      >
        <Button
          class="flex-1"
          variant="solid"
          theme="green"
          size="sm"
          @click="responseToCall('accept')"
          >Accept</Button
        >
        <Button
          class="flex-1"
          variant="solid"
          theme="red"
          size="sm"
          @click="responseToCall('refuse')"
          >Decline</Button
        >
      </div>

      <div class="flex justify-end mt-2">
        <Button
          v-if="(initiateCallResource.data && isOutgoing) || agentAnswered"
          variant="solid"
          theme="red"
          size="sm"
          @click="hangUpCall"
          >Hang up</Button
        >
      </div>

      <ErrorMessage :message="errorMessage" class="mt-2" />
    </div>

    <Button
      class="absolute -bottom-10 -right-5"
      variant="outline"
      theme="red"
      size="lg"
      icon="x"
      @click="direction = 'idle'"
    />
  </div>
</template>

<script setup>
import {
  Avatar,
  Button,
  createResource,
  ErrorMessage,
  toast,
  TextEditor,
} from 'frappe-ui'
import { onBeforeUnmount, reactive, ref, watch, nextTick, computed } from 'vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { globalStore } from '../../stores/global'
import NoteIcon from '@/components/Icons/NoteIcon.vue'

const callStatus = ref('')
const direction = ref('idle') // 'idle', 'incoming', 'outgoing'

const isIdle = computed(() => direction.value === 'idle')
const isIncoming = computed(() => direction.value === 'incoming')
const isOutgoing = computed(() => direction.value === 'outgoing')
const showCallPopup = computed(() => !isIdle.value)

const contactDetails = reactive({
  name: '',
  number: '',
  image: '',
})

const channelId = ref('')

const callStatusChangeState = ref('')

const errorMessage = ref('')
const callPopupHeader = ref(null)
const agentAnswered = ref(false)

// old

const callData = reactive({
  caller: '',
  channelId: '',
})
const ringtone = ref(null)
const showNote = ref(false)
const showTask = ref(false)
const note = ref({
  value: '',
  content: '',
})

const { $socket } = globalStore()
const { width, height } = useWindowSize()

const { x, y, style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 450 },
  preventDefault: true,
})

function hangUpCall() {
  createResource({
    url: 'crm.integrations.yeastar.api.hangup_call',
    params: { channel_id: channelId.value },
    auto: true,
    onSuccess() {
      toast.success('Call ended successfully')
      direction.value = 'idle'
    },
    onError() {
      toast.error('Error ending call')
      errorMessage.value = 'An error occurred while ending the call.'
    },
  })
}

function stateMap(state) {
  const states = {
    RING: 'Ringing',
    ANSWER: 'In Progress',
    BYE: 'Declined',
  }
  return states[state]
}

const initiateCallResource = createResource({
  url: 'crm.integrations.yeastar.api.make_call',
  makeParams() {
    return { callee: contactDetails.number }
  },
})

function makeOutgoingCall(number) {
  direction.value = 'outgoing'
  contactDetails.number = number
  callStatus.value = 'Connecting...'

  initiateCallResource.submit(
    {},
    {
      onSuccess(data) {
        callStatus.value = 'Success'
        console.log('data', data)
      },
      onError() {
        toast.error('Error initiating call')
        errorMessage.value = 'An error occurred while initiating the call.'
      },
    },
  )
}

function playAudio() {
  ringtone.value = new Audio(
    'http://soundbible.com/mp3/Air Plane Ding-SoundBible.com-496729130.mp3',
  )
  ringtone.value.loop = true
  ringtone.value.play()

  setTimeout(() => {
    stopAudio()
  }, 10000)
}

function createUpdateNote() {
  createResource({
    url: 'crm.integrations.api.add_note_to_call_log',
    params: {
      call_sid: callData.caller,
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

function stopAudio() {
  if (ringtone.value) {
    ringtone.value.pause()
    ringtone.value.currentTime = 0
    ringtone.value = null
    agentAnswered.value ? (direction.value = 'idle') : 'incoming'
  }
}

function setup() {
  initiateSockets()
}

function initiateSockets() {
  $socket.on('yeastar_incoming_call', (data) => {
    closeCallPopup()
    initiateIncomingCall(data)
  })
  $socket.on('yeastar_call_status_changed', (data) => {
    console.log('Call status changed:', data)
    channelId.value = data.channel_id
    callStatusChangeState.value = data.status
  })
}

function initiateIncomingCall(data) {
  contactDetails.number = data.caller
  channelId.value = data.channel_id
  callStatus.value = 'Incoming Call...'
  direction.value = 'incoming'

  playAudio()
}

function responseToCall(action) {
  handleCallResponse(action).submit(
    {},
    {
      onSuccess() {
        if (action === 'accept') {
          callStatus.value = 'Call Accepted'
          agentAnswered.value = true
        } else {
          callStatus.value = 'Call Declined'
          direction.value = 'idle'
        }
        stopAudio()
      },
      onError() {
        toast.error('Error responding to call')
        errorMessage.value = 'An error occurred while responding to the call.'
      },
    },
  )
}

const handleCallResponse = (action) =>
  createResource({
    url: 'crm.integrations.yeastar.api.respond_to_call',
    makeParams() {
      return { channel_id: callData.channelId, action: action }
    },
  })

function showNoteWindow() {
  showNote.value = !showNote.value
  updateWindowHeight(showNote.value)
  if (showNote.value) {
    showTask.value = false
  }
}

function updateWindowHeight(isOpening) {
  const offset = 224
  if (isOpening) {
    y.value = y.value - offset
  } else {
    y.value = y.value + offset
  }

  if (y.value < 10) y.value = 10
}

function closeCallPopup() {
  initiateCallResource.reset()
  errorMessage.value = ''
  contactDetails.number = ''
  callStatus.value = ''
  channelId.value = ''
  callStatusChangeState.value = ''
  agentAnswered.value = false
  stopAudio()
}

watch(callStatusChangeState, (newStatus) => {
  if (newStatus === 'BYE') {
    toast.info('Call Ended by Client')
    direction.value = 'idle'
  }
})

watch(showCallPopup, (newVal) => {
  if (!newVal) {
    closeCallPopup()
  }
})

onBeforeUnmount(() => {
  $socket.off('yeastar_incoming_call')
  $socket.off('yeastar_call_status_changed')
})

defineExpose({ makeOutgoingCall, setup })
</script>
