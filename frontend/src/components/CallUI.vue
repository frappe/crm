<template>
  <slot />
  <Dialog
    v-model="showPhoneCall"
    :options="{
      title: 'Make a call...',
      actions: [{ label: 'Make a call...', variant: 'solid' }],
    }"
  >
    <template #body-content>
      <div>Make a call to +917666980887</div>
    </template>
    <template #actions="{ close }">
      <div class="flex flex-row-reverse gap-2">
        <Button
          variant="solid"
          label="Make a call..."
          @click="makeOutgoingCall(close)"
        />
      </div>
    </template>
  </Dialog>
  <div
    v-if="showCallPopup"
    ref="callPopup"
    class="fixed select-none z-10 bg-gray-900 rounded-lg shadow-lg p-4 flex flex-col w-60"
    :style="style"
  >
    <div class="flex items-center flex-row-reverse gap-1">
      <DragIcon1 ref="callPopopHandle" class="w-4 h-4 cursor-move text-white" />
      <MinimizeIcon
        class="w-4 h-4 text-white cursor-pointer"
        @click="toggleCallWindow"
      />
    </div>
    <div class="flex flex-col justify-center items-center gap-2">
      <UserAvatar
        :user="getUser().name"
        class="flex items-center justify-center !h-24 !w-24 relative"
        :class="onCall || calling ? '' : 'pulse'"
      />
      <div class="text-xl font-medium text-white">
        {{ getUser().full_name }}
      </div>
      <div class="text-sm text-gray-500">+917666980887</div>
      <div class="text-white text-base my-1">
        {{
          onCall
            ? '0:38'
            : callStatus == 'ringing'
            ? 'Ringing...'
            : callStatus == 'initiated' || callStatus == 'calling'
            ? 'Calling...'
            : 'Incoming call...'
        }}
      </div>
      <div v-if="onCall" class="flex gap-2">
        <Button
          :icon="muted ? 'mic-off' : 'mic'"
          class="rounded-full"
          @click="toggleMute"
        />
        <Button class="rounded-full">
          <template #icon>
            <DialpadIcon class="rounded-full cursor-pointer" />
          </template>
        </Button>
        <Button class="rounded-full bg-red-600 hover:bg-red-700">
          <template #icon>
            <PhoneIcon
              class="text-white fill-white h-4 w-4 rotate-[135deg]"
              @click="hangUpCall"
            />
          </template>
        </Button>
      </div>
      <div v-else-if="calling">
        <Button
          size="md"
          variant="solid"
          theme="red"
          label="Cancel"
          @click="cancelCall"
        >
          <template #prefix>
            <PhoneIcon class="text-white fill-white h-4 w-4 rotate-[135deg]" />
          </template>
        </Button>
      </div>
      <div v-else class="flex gap-2 text-sm mt-2">
        <Button
          size="md"
          variant="solid"
          theme="green"
          label="Accept"
          @click="acceptIncomingCall"
        >
          <template #prefix>
            <PhoneIcon class="text-white fill-white h-4 w-4" />
          </template>
        </Button>
        <Button
          size="md"
          variant="solid"
          theme="red"
          label="Reject"
          @click="rejectIncomingCall"
        >
          <template #prefix>
            <PhoneIcon class="text-white fill-white h-4 w-4 rotate-[135deg]" />
          </template>
        </Button>
      </div>
    </div>
  </div>
  <Teleport v-if="showSmallCallWindow" to="#call-area">
    <div
      class="flex items-center justify-between p-1.5 gap-2 bg-gray-900 rounded m-2 cursor-pointer select-none"
      @click="toggleCallWindow"
    >
      <div class="inline-flex items-center gap-1.5 truncate">
        <UserAvatar
          :user="getUser().name"
          class="flex items-center justify-center"
        />
        <div class="text-base font-medium text-white truncate">
          Shariq Ansari
        </div>
      </div>
      <div v-if="onCall" class="flex items-center gap-1.5">
        <div class="text-white text-base my-1">0:38</div>
        <Button variant="solid" theme="red" class="rounded-full !h-6 !w-6">
          <template #icon>
            <PhoneIcon
              class="text-white fill-white h-3 w-3 rotate-[135deg]"
              @click.stop="hangUpCall"
            />
          </template>
        </Button>
      </div>
      <div v-else-if="calling" class="flex items-center gap-1.5">
        <div class="text-white text-base my-1">
          {{ callStatus == 'ringing' ? 'Ringing...' : 'Calling...' }}
        </div>
        <Button
          variant="solid"
          theme="red"
          class="rounded-full !h-6 !w-6"
          @click.stop="cancelCall"
        >
          <template #icon>
            <PhoneIcon class="text-white fill-white h-3 w-3 rotate-[135deg]" />
          </template>
        </Button>
      </div>
      <div v-else class="flex gap-1.5 text-sm">
        <Button
          variant="solid"
          theme="green"
          class="rounded-full !h-6 !w-6 pulse relative"
          @click.stop="acceptIncomingCall"
        >
          <template #icon>
            <PhoneIcon class="text-white fill-white h-3 w-3 animate-pulse" />
          </template>
        </Button>
        <Button
          variant="solid"
          theme="red"
          class="rounded-full !h-6 !w-6"
          @click.stop="rejectIncomingCall"
        >
          <template #icon>
            <PhoneIcon class="text-white fill-white h-3 w-3 rotate-[135deg]" />
          </template>
        </Button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import DragIcon1 from '@/components/Icons/DragIcon1.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { Device } from '@twilio/voice-sdk'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { onMounted, provide, ref, watch } from 'vue'

const { getUser } = usersStore()

let device = ''
let log = ref('Connecting...')
let _call = ref(null)
let showPhoneCall = ref(false)

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let muted = ref(false)
let callPopup = ref(null)
let callPopopHandle = ref(null)
let calling = ref(false)

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  handle: callPopopHandle,
  preventDefault: true,
})

async function startupClient() {
  log.value = 'Requesting Access Token...'

  try {
    const data = await call('crm.twilio.api.generate_access_token')
    log.value = 'Got a token.'
    intitializeDevice(data.token)
  } catch (err) {
    log.value = 'An error occurred. ' + err.message
  }
}

function intitializeDevice(token) {
  device = new Device(token, {
    codecPreferences: ['opus', 'pcmu'],
    fakeLocalDTMF: true,
    enableRingingState: true,
  })

  addDeviceListeners()

  device.register()
}

function addDeviceListeners() {
  device.on('registered', () => {
    log.value = 'Ready to make and receive calls!'
  })

  device.on('unregistered', (device) => {
    log.value = 'Logged out'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + error.message
  })

  device.on('incoming', handleIncomingCall)

  device.on('connect', (conn) => {
    conn
    debugger
    log.value = 'Successfully established call!'
  })
}

function toggleMute() {
  if (_call.value.isMuted()) {
    _call.value.mute(false)
    muted.value = false
  } else {
    _call.value.mute()
    muted.value = true
  }
}

function handleIncomingCall(call) {
  log.value = `Incoming call from ${call.parameters.From}`

  showCallPopup.value = true
  _call.value = call

  // add event listener to call object
  call.on('cancel', handleDisconnectedIncomingCall)
  call.on('disconnect', handleDisconnectedIncomingCall)
  call.on('reject', handleDisconnectedIncomingCall)
}

function acceptIncomingCall() {
  _call.value.accept()

  log.value = 'Accepted incoming call.'
  onCall.value = true
}

function rejectIncomingCall() {
  _call.value.reject()
  log.value = 'Rejected incoming call'
  showCallPopup.value = false
  showSmallCallWindow.value = false
  callStatus.value = ''
}

function hangUpCall() {
  _call.value.disconnect()
  log.value = 'Hanging up incoming call'
  onCall.value = false
  callStatus.value = ''
}

function handleDisconnectedIncomingCall() {
  log.value = `Call ended.`
  showCallPopup.value = false
  showSmallCallWindow.value = false
  _call.value = null
}

let callStatus = ref('')

async function makeOutgoingCall(close) {
  close()
  if (device) {
    log.value = `Attempting to call +917666980887 ...`

    try {
      _call.value = await device.connect({
        params: {
          To: '+917666980887',
        },
      })

      _call.value.on('messageReceived', (message) => {
        let info = message.content
        callStatus.value = info.CallStatus

        log.value = `Call status: ${info.CallStatus}`

        if (info.CallStatus == 'in-progress') {
          log.value = `Call in progress.`
          showCallPopup.value = true
          calling.value = false
          onCall.value = true
        }
      })

      _call.value.on('accept', () => {
        log.value = `Initiated call!`
        showCallPopup.value = true
        calling.value = true
        onCall.value = false
        callStatus.value = 'calling'
      })
      _call.value.on('disconnect', () => {
        log.value = `Call ended.`
        calling.value = false
        onCall.value = false
        showCallPopup.value = false
        showSmallCallWindow = false
        _call.value = null
        callStatus.value = ''
      })
      _call.value.on('cancel', () => {
        log.value = `Call ended.`
        calling.value = false
        onCall.value = false
        showCallPopup.value = false
        showSmallCallWindow = false
        _call.value = null
        callStatus.value = ''
      })
    } catch (error) {
      log.value = `Could not connect call: ${error.message}`
    }
  } else {
    log.value = 'Unable to make call.'
  }
}

function cancelCall() {
  _call.value.disconnect()
  showCallPopup.value = false
  if (showSmallCallWindow.value) {
    showSmallCallWindow.value = false
  }
  calling.value = false
  onCall.value = false
  callStatus.value = ''
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  if (showCallPopup.value) {
    showSmallCallWindow.value = false
  } else {
    showSmallCallWindow.value = true
  }
}

onMounted(() => startupClient())

watch(
  () => log.value,
  (value) => {
    console.log(value)
  },
  { immediate: true }
)

provide('showPhoneCall', showPhoneCall)
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
