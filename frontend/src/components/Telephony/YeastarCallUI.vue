<template>
  <div
    v-show="showCallPopup"
    :style="style"
    @click.stop
    ref="callPopupHeader"
    class="fixed z-20 cursor-pointer"
  >
    <div
      class="w-[300px] rounded-2xl bg-gray-900 shadow-2xl p-4 text-white border border-gray-800"
    >
      <div class="flex items-center gap-3 mb-4">
        <div
          class="h-9 w-9 flex items-center justify-center rounded-full bg-blue-600/20"
        >
          <PhoneIcon class="h-4 w-4 text-blue-500 animate-pulse" />
        </div>

        <div class="flex flex-col">
          <span class="text-sm text-gray-400">Call Status</span>
          <span class="font-semibold text-lg leading-tight">
            {{ callStatus }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-4 mb-4">
        <Avatar shape="circle" label="U" size="lg" />

        <div class="flex flex-col">
          <span class="font-medium text-white"></span>
          <small>Yeastar</small>
          <span class="text-sm text-gray-400">
            ({{ calleeNumber ? calleeNumber : callData.caller }})
          </span>
        </div>
      </div>

      <div
        v-show="resourceStatus"
        class="mt-3 rounded-lg bg-gray-800/60 px-3 py-2 text-sm text-gray-300"
      >
        <span class="text-green-400 font-medium"> Connection successful </span>
        <div class="text-xs mt-1 text-gray-400">
          Pick up your Yeastar IP phone to start the call
        </div>
      </div>

      <div
        v-show="incomingCall"
        class="flex flex-row p-2 border-white justify-between"
      >
        <Button
          class=""
          variant="solid"
          theme="green"
          size="sm"
          @click="responseToCall('accept')"
          >Accept</Button
        >
        <Button
          class=" "
          variant="solid"
          theme="red"
          size="sm"
          @click="responseToCall('refuse')"
          >Decline</Button
        >
      </div>
      <ErrorMessage :message="errorMessage" />
    </div>
    <Button
      class="absolute -bottom-10 -right-5"
      variant="subtle"
      theme="red"
      size="lg"
      icon="x"
      @click="showCallPopup = false"
    />
  </div>
</template>

<script setup>
import {
  Alert,
  Avatar,
  Button,
  call,
  createResource,
  ErrorMessage,
  toast,
} from 'frappe-ui'
import { nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { globalStore } from '../../stores/global'

const showCallPopup = ref(false)
const callPopupHeader = ref(null)
const calleeNumber = ref('')
const callStatus = ref('')
const errorMessage = ref('')
const resourceStatus = ref(null)
const contact = reactive({
  name: '',
  image: '',
})
const callData = reactive({
  caller: '',
  channelId: '',
})
const incomingCall = ref(false)

const { $socket } = globalStore()

function makeOutgoingCall(number) {
  showCallPopup.value = true
  calleeNumber.value = number
  callStatus.value = 'Connecting...'
  createResource({
    url: 'crm.integrations.yeastar.api.make_call',
    params: { callee: number },
    auto: true,
    onSuccess(response) {
      callStatus.value = 'Connected'
      resourceStatus.value = true
    },
    onError(error) {
      toast.error('Error initiating call')
      errorMessage.value = 'An error occurred while initiating the call.'
    },
  })
}

function playAudio() {
  const playAudio = new Audio(
    'http://soundbible.com/mp3/Air Plane Ding-SoundBible.com-496729130.mp3',
  )
  playAudio.play()
}

function setup() {
  $socket.on('yeastar_incoming_call', (data) => {
    callData.caller = data.caller
    callData.channelId = data.channel_id
    callStatus.value = 'Incoming Call...'
    incomingCall.value = true
    showCallPopup.value = true
    playAudio()
  })
}

function responseToCall(action) {
  handleCallResponse(action).submit(
    {},
    {
      onSuccess(response) {
        incomingCall.value = false
        callStatus.value =
          action === 'accept' ? 'Call Accepted' : 'Call Declined'
        resourceStatus.value =
          action === 'accept' ? true : 'Call has been declined.'
      },
      onError(error) {
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

const { width, height } = useWindowSize()

watch(showCallPopup, (newVal) => {
  if (!newVal) {
    errorMessage.value = ''
    calleeNumber.value = ''
    callStatus.value = ''
  }
})

let { style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 250 },
  preventDefault: true,
})

onBeforeUnmount(() => {
  $socket.off('yeastar_incoming_call')
})
defineExpose({ makeOutgoingCall, setup })
</script>
