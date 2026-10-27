<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-72 cursor-move select-none flex-col rounded-6 bg-surface-gray-10 p-4 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="relative flex items-center justify-center [&>div]:text-[30px]"
          :class="[
            onCall || calling ? '' : 'pulse',
            onCall ? '!h-16 !w-16 [&>div]:!text-[20px]' : '!h-24 !w-24',
          ]"
        />
        <div class="flex flex-col items-center justify-center gap-1">
          <div class="text-2xl-medium">
            {{ contact?.full_name ?? __('Unknown') }}
          </div>
          <div class="text-sm text-ink-gray-5">{{ contact?.mobile_no }}</div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base">
          {{
            callStatus == 'initiating'
              ? __('Initiating call...')
              : callStatus == 'ringing'
                ? __('Ringing...')
                : calling
                  ? __('Calling...')
                  : __('Incoming call...')
          }}
        </div>

        <!-- Live Transcript Area -->
        <div
          v-if="onCall || utterances.length > 0"
          class="flex w-full flex-col gap-1.5 rounded-lg bg-surface-gray-9/70 p-2.5 text-left border border-surface-gray-7/50"
        >
          <div
            class="flex items-center justify-between text-[11px] font-semibold text-ink-gray-4 uppercase tracking-wider"
          >
            <div class="flex items-center gap-1.5">
              <span
                class="size-2 rounded-full"
                :class="
                  transcriptionStatus === 'error'
                    ? 'bg-amber-500'
                    : 'bg-emerald-500 animate-pulse'
                "
              />
              <span>{{ __('Live Transcript') }}</span>
            </div>
            <span
              v-if="transcriptionStatus === 'error'"
              class="text-[10px] lowercase text-ink-gray-5"
            >
              {{ __('unavailable') }}
            </span>
          </div>

          <div
            ref="transcriptContainer"
            class="flex max-h-48 min-h-[72px] w-full flex-col gap-2 overflow-y-auto pr-1 text-xs select-text scroll-smooth"
          >
            <div
              v-if="utterances.length === 0"
              class="flex h-full min-h-[60px] items-center justify-center text-center text-ink-gray-5 italic text-[11px]"
            >
              {{
                transcriptionStatus === 'error'
                  ? __('Live transcription unavailable')
                  : __('Listening for speech...')
              }}
            </div>

            <div
              v-for="(item, index) in utterances"
              :key="index"
              class="flex flex-col gap-0.5"
            >
              <div
                class="text-[11px] font-semibold"
                :class="
                  item.speaker === 'agent'
                    ? 'text-blue-400'
                    : 'text-emerald-400'
                "
              >
                {{ item.speaker === 'agent' ? __('Agent') : __('Customer') }}
              </div>
              <div
                class="rounded bg-surface-gray-8/60 px-2 py-1 text-ink-gray-2 leading-relaxed whitespace-pre-wrap break-words"
                :class="{ 'opacity-75 italic': !item.isFinal }"
              >
                {{ item.text }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="onCall" class="flex gap-2">
          <Button
            :icon="muted ? 'lucide-mic-off' : 'lucide-mic'"
            class="rounded-full"
            @click="toggleMute"
          />
          <Button
            class="cursor-pointer rounded-full"
            :class="{ 'bg-surface-gray-7': showKeypad }"
            :tooltip="__('Dialpad')"
            :icon="DialpadIcon"
            @click="toggleKeypad"
          />
          <Button
            class="cursor-pointer rounded-full"
            :tooltip="__('Add a Note')"
            :icon="NoteIcon"
            @click="openNoteModal"
          />
          <Button
            class="rounded-full bg-surface-red-7 hover:bg-surface-red-8 rotate-[135deg] text-ink-base"
            :tooltip="__('Hang Up')"
            :icon="PhoneIcon"
            @click="hangUpCall"
          />
        </div>
        <div
          v-if="onCall && showKeypad"
          class="grid w-full grid-cols-3 gap-2 pt-1"
        >
          <Button
            v-for="digit in keypadDigits"
            :key="digit"
            variant="subtle"
            class="!h-9 justify-center text-base font-medium"
            :label="digit"
            @click="sendDigit(digit)"
          />
        </div>
        <div v-else-if="calling || callStatus == 'initiating'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            class="rounded-6 text-ink-base"
            :disabled="callStatus == 'initiating'"
            @click="cancelCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="__('Accept')"
            class="rounded-6 text-ink-base"
            :iconLeft="PhoneIcon"
            @click="acceptIncomingCall"
          />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Reject')"
            class="rounded-6 text-ink-base"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <div
    v-show="showSmallCallWindow"
    class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-6 bg-surface-gray-10 px-2 py-[7px] text-base text-ink-gray-2"
    v-bind="$attrs"
    @click="toggleCallWindow"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate">
        {{ contact?.full_name ?? __('Unknown') }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :icon="PhoneIcon"
        @click.stop="hangUpCall"
      />
    </div>
    <div v-else-if="calling" class="flex items-center gap-3">
      <div class="my-1">
        {{ callStatus == 'ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :icon="PhoneIcon"
        @click.stop="cancelCall"
      />
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full animate-pulse text-ink-base"
        :tooltip="__('Accept Call')"
        :icon="PhoneIcon"
        @click.stop="acceptIncomingCall"
      />
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-base"
        :tooltip="__('Reject Call')"
        :icon="PhoneIcon"
        @click.stop="rejectIncomingCall"
      />
    </div>
  </div>
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { Device } from '@twilio/voice-sdk'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { globalStore } from '@/stores/global'
import {
  formatTranscriptUtterances,
  appendOrUpdateUtterance,
} from '@/utils/callTranscript'
import { Avatar, call, createResource } from 'frappe-ui'
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const { capture } = useTelemetry()
const { $socket } = globalStore()

let device = ''
let log = ref('Connecting...')
let _call = null

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let muted = ref(false)
let showKeypad = ref(false)
let callPopup = ref(null)
let counterUp = ref(null)
let callStatus = ref('')

const activeCallSid = ref('')
const utterances = ref([])
const transcriptionStatus = ref('idle')
const transcriptContainer = ref(null)
let transcriptSaved = false

const keypadDigits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

const phoneNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

const { showModal } = useDoctypeModal()
const note = ref({
  name: '',
  title: '',
  content: '',
})

function openNoteModal() {
  showModal({
    name: note.value.name || null,
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: (n) => updateNote(n, true),
      afterUpdate: updateNote,
    },
  })
}

async function updateNote(_note, isInsert = false) {
  note.value = _note
  const sid = activeCallSid.value || _call?.parameters?.CallSid
  if (isInsert && _note.name && sid) {
    await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: sid,
      note: _note,
    })
    capture('note_created')
  } else {
    capture('note_updated')
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 320, y: height.value - 380 },
  preventDefault: true,
})

function handleLiveTranscriptEvent(data) {
  if (!data || !data.text) return

  // Filter out if not for this call
  if (activeCallSid.value && data.call_sid && data.call_sid !== activeCallSid.value) {
    return
  }
  if (!activeCallSid.value && data.call_sid) {
    activeCallSid.value = data.call_sid
  }

  transcriptionStatus.value = 'listening'

  utterances.value = appendOrUpdateUtterance(utterances.value, {
    speaker: data.speaker,
    text: data.text,
    isFinal: data.is_final,
    timestamp: data.timestamp,
  })

  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (transcriptContainer.value) {
      transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
    }
  })
}

async function saveFinalTranscript() {
  if (transcriptSaved) return
  const sid = activeCallSid.value || _call?.parameters?.CallSid
  if (!sid || utterances.value.length === 0) return

  transcriptSaved = true
  const formatted = formatTranscriptUtterances(utterances.value)

  try {
    await call('crm.integrations.twilio.api.save_call_transcript', {
      call_sid: sid,
      transcript: formatted,
    })
  } catch (err) {
    console.error('Failed to save call transcript to CRM:', err)
  }
}

function resetTranscriptState() {
  utterances.value = []
  activeCallSid.value = ''
  transcriptionStatus.value = 'idle'
  transcriptSaved = false
}

function handleSocketMessage(data) {
  if (!data) return
  if (data.event === 'started') {
    transcriptionStatus.value = 'listening'
    return
  }
  if (data.event === 'stopped') {
    return
  }
  if (data.event === 'content') {
    handleLiveTranscriptEvent(data)
  }
}

function setupSocket() {
  if ($socket) {
    $socket.on('twilio_transcription', handleSocketMessage)
  }
}

onMounted(() => {
  setupSocket()
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('twilio_transcription', handleSocketMessage)
  }
})

async function startupClient() {
  log.value = 'Requesting Access Token...'

  try {
    setupSocket()
    const data = await call('crm.integrations.twilio.api.generate_access_token')
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

  device.on('unregistered', () => {
    log.value = 'Logged out'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + error.message
  })

  device.on('incoming', handleIncomingCall)

  device.on('tokenWillExpire', async () => {
    const data = await call('crm.integrations.twilio.api.generate_access_token')
    device.updateToken(data.token)
  })
}

function toggleMute() {
  if (_call.isMuted()) {
    _call.mute(false)
    muted.value = false
  } else {
    _call.mute()
    muted.value = true
  }
}

function toggleKeypad() {
  showKeypad.value = !showKeypad.value
}

function sendDigit(digit) {
  if (_call && onCall.value) {
    _call.sendDigits(digit)
  }
}

function handleIncomingCall(call) {
  resetTranscriptState()
  log.value = `Incoming call from ${call.parameters.From}`
  phoneNumber.value = call.parameters.From

  showCallPopup.value = true
  _call = call
  if (call.parameters?.CallSid) {
    activeCallSid.value = call.parameters.CallSid
  }

  _call.on('accept', (conn) => {
    console.log('conn', conn)
    if (_call?.parameters?.CallSid) {
      activeCallSid.value = _call.parameters.CallSid
    }
  })

  // add event listener to call object
  call.on('cancel', handleDisconnectedIncomingCall)
  call.on('disconnect', handleDisconnectedIncomingCall)
  call.on('reject', handleDisconnectedIncomingCall)
}

async function acceptIncomingCall() {
  log.value = 'Accepted incoming call.'
  onCall.value = true
  if (_call?.parameters?.CallSid) {
    activeCallSid.value = _call.parameters.CallSid
  }
  await _call.accept()
  counterUp.value.start()
}

function rejectIncomingCall() {
  _call.reject()
  log.value = 'Rejected incoming call'
  showCallPopup.value = false
  showSmallCallWindow.value = false
  showKeypad.value = false

  callStatus.value = ''
  muted.value = false
  resetTranscriptState()
}

async function hangUpCall() {
  await saveFinalTranscript()
  _call.disconnect()
  log.value = 'Hanging up incoming call'
  onCall.value = false
  callStatus.value = ''
  muted.value = false
  showKeypad.value = false
  note.value = {
    name: '',
    title: '',
    content: '',
  }
  counterUp.value.stop()
  resetTranscriptState()
}

async function handleDisconnectedIncomingCall() {
  log.value = `Call ended from handle disconnected Incoming call.`
  await saveFinalTranscript()
  showCallPopup.value = false
  showSmallCallWindow.value = false
  showKeypad.value = false
  _call = null
  muted.value = false
  onCall.value = false
  counterUp.value.stop()
  resetTranscriptState()
}

async function makeOutgoingCall(number) {
  phoneNumber.value = number
  resetTranscriptState()

  if (device) {
    log.value = `Attempting to call ${number} ...`

    try {
      _call = await device.connect({
        params: { To: number },
      })
      if (_call.parameters?.CallSid) {
        activeCallSid.value = _call.parameters.CallSid
      }

      showCallPopup.value = true
      callStatus.value = 'initiating'

      capture('make_outgoing_call')

      _call.on('messageReceived', (message) => {
        let info = message.content
        callStatus.value = info.CallStatus
        if (info.ParentCallSid) {
          activeCallSid.value = info.ParentCallSid
        } else if (info.CallSid && !activeCallSid.value) {
          activeCallSid.value = info.CallSid
        }

        log.value = `Call status: ${info.CallStatus}`

        if (info.CallStatus == 'in-progress') {
          log.value = `Call in progress.`
          calling.value = false
          onCall.value = true
          counterUp.value.start()
        }
      })

      _call.on('accept', () => {
        log.value = `Initiated call!`
        showCallPopup.value = true
        calling.value = true
        onCall.value = false
        if (_call?.parameters?.CallSid) {
          activeCallSid.value = _call.parameters.CallSid
        }
      })
      _call.on('disconnect', async () => {
        log.value = `Call ended from makeOutgoing call disconnect.`
        await saveFinalTranscript()
        calling.value = false
        onCall.value = false
        showCallPopup.value = false
        showSmallCallWindow.value = false
        showKeypad.value = false
        _call = null
        callStatus.value = ''
        muted.value = false
        counterUp.value.stop()
        note.value = {
          name: '',
          title: '',
          content: '',
        }
        resetTranscriptState()
      })
      _call.on('cancel', () => {
        log.value = `Call ended from makeOutgoing call cancel.`
        calling.value = false
        onCall.value = false
        showCallPopup.value = false
        showSmallCallWindow.value = false
        showKeypad.value = false
        _call = null
        callStatus.value = ''
        muted.value = false
        note.value = {
          name: '',
          title: '',
          content: '',
        }
        counterUp.value.stop()
        resetTranscriptState()
      })
    } catch (error) {
      log.value = `Could not connect call: ${error.message}`
      transcriptionStatus.value = 'error'
    }
  } else {
    log.value = 'Unable to make call.'
  }
}

function cancelCall() {
  _call.disconnect()
  showCallPopup.value = false
  showSmallCallWindow.value = false
  calling.value = false
  onCall.value = false
  showKeypad.value = false
  callStatus.value = ''
  muted.value = false
  note.value = {
    name: '',
    title: '',
    content: '',
  }
  resetTranscriptState()
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
}

watch(onCall, (value) => {
  if (!value) {
    showKeypad.value = false
  }
})

watch(
  () => log.value,
  (value) => {
    console.log(value)
  },
  { immediate: true },
)

defineExpose({ makeOutgoingCall, setup: startupClient })
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
