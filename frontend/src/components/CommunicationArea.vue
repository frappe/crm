<template>
  <div class="max-w-[81.7%] pl-16 p-4 pt-2">
    <button
      class="flex gap-2 w-full items-center rounded-lg p-1 bg-gray-100 hover:bg-gray-200"
      @click="showCommunicationBox = true"
      v-show="!showCommunicationBox"
    >
      <UserAvatar class="m-1" :user="getUser().name" size="sm" />
      <div class="flex-1 text-left text-base text-gray-600">Add a reply...</div>
      <Tooltip text="Make a call..." class="m-1">
        <PhoneIcon
          class="bg-gray-900 rounded-full text-white fill-white p-[3px]"
          @click.stop="openPhoneCallDialog"
        />
      </Tooltip>
    </button>
    <div
      v-show="showCommunicationBox"
      class="w-full rounded-lg border bg-white p-4 focus-within:border-gray-400"
      @keydown.ctrl.enter.capture.stop="submitComment"
      @keydown.meta.enter.capture.stop="submitComment"
    >
      <div class="mb-4 flex items-center">
        <UserAvatar :user="getUser().name" size="sm" />
        <span class="ml-2 text-base font-medium text-gray-900">
          {{ getUser().full_name }}
        </span>
      </div>
      <EmailEditor
        ref="newEmailEditor"
        :value="newEmail"
        @change="onNewEmailChange"
        :submitButtonProps="{
          variant: 'solid',
          onClick: submitComment,
          disabled: emailEmpty,
        }"
        :discardButtonProps="{
          onClick: () => {
            showCommunicationBox = false
            newEmail = ''
          },
        }"
        :editable="showCommunicationBox"
        v-model="modelValue.data"
        placeholder="Add a reply..."
      />
    </div>
  </div>
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
          @click="makeOutgoingCall"
        />
      </div>
    </template>
  </Dialog>
  <div
    v-show="showIncomingCall"
    ref="incomingCallPopup"
    class="fixed select-none z-10 bg-white rounded-lg shadow-lg p-4 flex flex-col gap-4 w-60"
    :style="style"
  >
    <div class="flex items-center justify-between">
      <div>Incoming Call...</div>
      <DragIcon ref="incomingCallHandle" class="w-4 h-4 cursor-move" />
    </div>
    <div class="flex flex-col justify-center items-center gap-2">
      <UserAvatar
        :user="getUser().name"
        class="flex items-center justify-center !h-24 !w-24 relative pulse"
      />
      <div class="text-xl font-medium">{{ getUser().full_name }}</div>
      <div class="text-sm text-gray-500">+917666980887</div>
      <div v-if="onCall" class="flex gap-2">
        <Button :icon="muted ? 'mic-off' : 'mic'" @click="toggleMute" />
        <Button
          variant="solid"
          theme="red"
          icon="phone-off"
          @click="rejectIncomingCall"
        />
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
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailEditor from '@/components/EmailEditor.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { usersStore } from '@/stores/users'
import { Tooltip, Dialog, call } from 'frappe-ui'
import { ref, watch, computed, defineModel } from 'vue'
import { Device } from '@twilio/voice-sdk'
import { useDraggable, useWindowSize } from '@vueuse/core'
import DragIcon from '@/components/Icons/DragIcon.vue'

const modelValue = defineModel()

const { getUser } = usersStore()

const showCommunicationBox = ref(false)
const newEmail = ref('')
const newEmailEditor = ref(null)

watch(
  () => showCommunicationBox.value,
  (value) => {
    if (value) {
      newEmailEditor.value.editor.commands.focus()
    }
  }
)

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === '<p></p>'
})

const onNewEmailChange = (value) => {
  newEmail.value = value
}

async function sendMail() {
  await call('frappe.core.doctype.communication.email.make', {
    recipients: modelValue.value.data.email,
    cc: '',
    bcc: '',
    subject: 'Email from Agent',
    content: newEmail.value,
    doctype: 'CRM Lead',
    name: modelValue.value.data.name,
    send_email: 1,
    sender: getUser().name,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function submitComment() {
  if (emailEmpty.value) return
  showCommunicationBox.value = false
  await sendMail()
  newEmail.value = ''
  modelValue.value.reload()
}

let device = ''
let log = ref('Connecting...')
let incomingCall = ref(null)
let showPhoneCall = ref(false)

let showIncomingCall = ref(false)
let onCall = ref(false)
let muted = ref(false)
let incomingCallPopup = ref(null)
let incomingCallHandle = ref(null)

const { width, height } = useWindowSize()

let { style } = useDraggable(incomingCallPopup, {
  initialValue: { x: width.value - 280, y: height.value - 300 },
  handle: incomingCallHandle,
  preventDefault: true,
})

function openPhoneCallDialog() {
  showPhoneCall.value = true
  startupClient()
}

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
    log.value = 'Successfully established call!'
  })
}

function toggleMute() {
  if (incomingCall.value.isMuted()) {
    incomingCall.value.mute(false)
    muted.value = false
  } else {
    incomingCall.value.mute()
    muted.value = true
  }
}

function handleIncomingCall(call) {
  log.value = `Incoming call from ${call.parameters.From}`

  showIncomingCall.value = true
  incomingCall.value = call

  // add event listener to call object
  call.on('cancel', handleDisconnectedIncomingCall)
  call.on('disconnect', handleDisconnectedIncomingCall)
  call.on('reject', handleDisconnectedIncomingCall)
}

function acceptIncomingCall() {
  incomingCall.value.accept()

  log.value = 'Accepted incoming call.'
  onCall.value = true
}

function rejectIncomingCall() {
  incomingCall.value.reject()
  log.value = 'Rejected incoming call'
  showIncomingCall.value = false
}

function handleDisconnectedIncomingCall() {
  log.value = `Call ended.`
  showIncomingCall.value = false
  incomingCall.value = null
}

async function makeOutgoingCall() {
  if (device) {
    log.value = `Attempting to call +917666980887 ...`

    try {
      const call = await device.connect({
        params: {
          To: '+917666980887',
        },
      })
    } catch (error) {
      log.value = `Could not connect call: ${error.message}`
    }
  } else {
    log.value = 'Unable to make call.'
  }
}

watch(
  () => log.value,
  (value) => {
    console.log(value)
  },
  { immediate: true }
)
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
