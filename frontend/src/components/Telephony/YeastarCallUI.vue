<template>
  <div v-show="showCallPopup" :style="style" @click.stop class="fixed z-20">
    <div
      class="w-[300px] rounded-2xl bg-gray-900 shadow-2xl p-4 text-white border border-gray-800"
    >
      <div>
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
            <div class="flex flex-col">
              <div>
                <span class="text-sm text-gray-400">
                  ({{ contactDetails.number }})
                </span>
                <small>{{ stateMap(callStatusChangeState) }}....</small>
              </div>
              <small v-show="isCallActive">
                {{ counterUpTimer?.updatedTime }}
              </small>
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
    <CountUpTimer ref="counterUpTimer" />
  </div>
</template>

<script setup>
import {
  Avatar,
  Button,
  call,
  createResource,
  ErrorMessage,
  toast,
} from 'frappe-ui'
import { onBeforeUnmount, reactive, ref, watch, computed, onMounted } from 'vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { globalStore } from '../../stores/global'
import CountUpTimer from '../CountUpTimer.vue'

const callStatus = ref('')
const direction = ref('idle') // 'idle', 'incoming', 'outgoing'

const isIdle = computed(() => direction.value === 'idle')
const isIncoming = computed(() => direction.value === 'incoming')
const isOutgoing = computed(() => direction.value === 'outgoing')
const showCallPopup = computed(() => !isIdle.value)
const isCallActive = computed(() => callStatus.value === 'ANSWER')
const callDuration = ref(0)

const contactDetails = reactive({
  name: '',
  number: '',
  image: '',
})

const channelId = ref('')
const activeChannelId = ref('')

const callStatusChangeState = ref('')

const errorMessage = ref('')
const callPopupHeader = ref(null)
const agentAnswered = ref(false)
const ringtone = ref(null)

const counterUpTimer = ref(null)

const { $socket } = globalStore()
const { width, height } = useWindowSize()

const { style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 450 },
  preventDefault: true,
})

function hangUpCall() {
  let currentChannelId

  activeChannelId.value
    ? (currentChannelId = activeChannelId.value)
    : (currentChannelId = channelId.value)

  createResource({
    url: 'crm.integrations.yeastar.api.hangup_call',
    params: { channel_id: currentChannelId },
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

function createCallLogEntry() {
  let durationInSeconds = counterUpTimer.value.timeToSeconds(callDuration.value)
  createResource({
    url: 'crm.integrations.api.create_call_log_entry',
    makeParams() {
      return {
        telephony_medium: 'Yeastar',
        status: 'Completed',
        type: isOutgoing.value ? 'Outgoing' : 'Incoming',
        from: isOutgoing.value ? 'session_user' : contactDetails.number,
        to: isOutgoing.value ? contactDetails.number : 'session_user',
        duration: durationInSeconds,
      }
    },
    onSuccess() {
      callStatus.value = ''
      direction.value = 'idle'
    },
    onError() {
      toast.error('Error creating call log entry')
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

function stopAudio() {
  if (ringtone.value) {
    ringtone.value.pause()
    ringtone.value.currentTime = 0
    ringtone.value = null
    agentAnswered.value
      ? (direction.value = 'incoming')
      : (direction.value = 'idle')
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
    if (!activeChannelId.value && direction.value === 'outgoing') {
      activeChannelId.value = data.channel_id
    }
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
          counterUpTimer.value.start()
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
      return { channel_id: channelId.value, action: action }
    },
  })

function closeCallPopup() {
  initiateCallResource.reset()
  errorMessage.value = ''
  contactDetails.number = ''
  callStatus.value = ''
  channelId.value = ''
  callStatusChangeState.value = ''
  agentAnswered.value = false
  activeChannelId.value = ''
  callDuration.value = 0

  stopAudio()
}

watch(callStatusChangeState, (newStatus) => {
  if (newStatus === 'BYE') {
    direction.value = 'idle'
  }
})

watch(showCallPopup, (newVal) => {
  if (!newVal) {
    if (isCallActive.value) {
      callDuration.value = counterUpTimer.value.stop()
      createCallLogEntry()
    } else {
      closeCallPopup()
    }
  }
})

onBeforeUnmount(() => {
  $socket.off('yeastar_incoming_call')
  $socket.off('yeastar_call_status_changed')
})

defineExpose({ makeOutgoingCall, setup })
</script>
