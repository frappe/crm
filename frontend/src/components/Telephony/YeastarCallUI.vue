<template>
  <div
    v-if="showCallPopup"
    ref="callPopupWrapper"
    :style="style"
    @click.stop
    class="fixed z-20"
  >
    <div
      ref="callPopupContainer"
      class="relative rounded-2xl bg-gray-900 shadow-2xl text-white border border-gray-800 transition-all duration-300"
      :class="showNote ? 'w-[300px]' : 'w-[300px]'"
    >
      <div v-show="!showNote" ref="callPopupHeader" class="p-4">
        <div
          class="flex items-center gap-3 mb-4 cursor-move active:cursor-grabbing select-none"
        >
          <span
            class="h-2 w-2 shrink-0 rounded-full"
            :class="[stateStyle.dot, stateStyle.pulse && 'animate-pulse']"
          />
          <div class="flex flex-col min-w-0">
            <span class="text-xs uppercase tracking-wide text-gray-500">
              {{ isIncoming ? 'Incoming call' : 'Outgoing call' }}
            </span>
            <span
              class="font-semibold text-base leading-tight truncate"
              :class="stateStyle.text"
            >
              {{ stateLabel }}
            </span>
          </div>
          <span
            v-if="isCallActive || isOnHold"
            class="ml-auto font-mono text-sm tabular-nums text-gray-300"
          >
            {{ counterUpTimer?.updatedTime }}
          </span>
        </div>

        <div class="flex gap-3 items-center">
          <Avatar
            shape="circle"
            :label="contactDetails.full_name || contactDetails.number || 'U'"
            :image="contactDetails.image"
            size="lg"
          />
          <div class="flex flex-col min-w-0">
            <span class="font-medium text-white truncate">
              {{
                contactDetails.full_name || contactDetails.number || 'Unknown'
              }}
            </span>
            <span
              v-if="contactDetails.full_name && contactDetails.number"
              class="text-sm text-gray-400 truncate"
            >
              {{ contactDetails.number }}
            </span>
            <span class="text-xs text-gray-500"
              >Yeastar · {{ agentNumber }}</span
            >
          </div>
        </div>

        <div
          v-if="handsetHint"
          class="mt-3 rounded-lg bg-gray-800/60 px-3 py-2 text-xs text-gray-400"
        >
          {{ handsetHint }}
        </div>

        <div
          v-if="isScreening && !isEnded"
          class="flex flex-row mt-3 justify-between gap-2"
        >
          <Button
            class="flex-1"
            variant="solid"
            theme="green"
            size="sm"
            :loading="responding === 'accept'"
            :disabled="!!responding"
            @click="responseToCall('accept')"
            >Accept</Button
          >
          <Button
            class="flex-1"
            variant="solid"
            theme="red"
            size="sm"
            :loading="responding === 'refuse'"
            :disabled="!!responding"
            @click="responseToCall('refuse')"
            >Decline</Button
          >
        </div>

        <div v-else-if="!isEnded" class="flex justify-end mt-3">
          <Button
            variant="solid"
            theme="red"
            size="sm"
            :loading="hangingUp"
            @click="hangUpCall"
            >Hang up</Button
          >
        </div>

        <ErrorMessage :message="errorMessage" class="mt-2" />
      </div>

      <div class="p-4" v-show="showNote">
        <div class="mb-3">
          <h3 class="text-lg font-semibold">Call Notes</h3>
        </div>
        <TextEditor
          variant="ghost"
          ref="content"
          editor-class="prose-sm h-[290px] text-ink-white overflow-auto mt-1"
          :bubbleMenu="true"
          :content="note.content"
          @change="(val) => (note.content = val)"
          :placeholder="__('Take a note...')"
        />
        <div class="flex flex-row justify-end gap-2 mt-3">
          <Button
            v-if="note?.content && note.content != '<p></p>'"
            size="sm"
            class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
            @click="saveNote"
            variant="solid"
            :label="__('Save')"
          />
        </div>
      </div>
    </div>

    <div class="flex justify-between">
      <Button
        class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
        :tooltip="showNote ? __('Hide notes') : __('Add a note')"
        size="md"
        :icon="NoteIcon"
        @click="toggleNoteWindow"
      />
    </div>

    <CountUpTimer ref="counterUpTimer" />
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
import { onBeforeUnmount, reactive, ref, watch, computed } from 'vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { globalStore } from '../../stores/global'
import { sessionStore } from '@/stores/session'
import CountUpTimer from '../CountUpTimer.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'

const STATE_STYLES = {
  dialing: { dot: 'bg-blue-500', text: 'text-white', pulse: true },
  connecting: { dot: 'bg-blue-500', text: 'text-white', pulse: true },
  ringing: { dot: 'bg-amber-400', text: 'text-white', pulse: true },
  in_progress: { dot: 'bg-green-500', text: 'text-white', pulse: false },
  on_hold: { dot: 'bg-amber-400', text: 'text-gray-300', pulse: false },
  ended: { dot: 'bg-gray-500', text: 'text-gray-400', pulse: false },
}

const DISMISS_AFTER_END_MS = 2500
const HANGUP_FALLBACK_MS = 4000

const direction = ref('idle')
const showNote = ref(false)

const callState = ref('')
const callStateLabel = ref('')

const isIdle = computed(() => direction.value === 'idle')
const isIncoming = computed(() => direction.value === 'incoming')
const isOutgoing = computed(() => direction.value === 'outgoing')
const showCallPopup = computed(() => !isIdle.value)
const isCallActive = computed(() => callState.value === 'in_progress')
const isOnHold = computed(() => callState.value === 'on_hold')
const isEnded = computed(() => callState.value === 'ended')

const stateLabel = computed(
  () =>
    callStateLabel.value || (isIncoming.value ? 'Incoming call' : 'Connecting'),
)
const stateStyle = computed(
  () => STATE_STYLES[callState.value] ?? STATE_STYLES.connecting,
)

const handsetHint = computed(() => {
  if (isOutgoing.value && ['dialing', 'connecting'].includes(callState.value))
    return 'Pick up your Yeastar handset — the customer is dialled once you answer.'
  if (isScreening.value)
    return 'Accept routes this call to your inbound destination. Decline drops it for the caller.'
  if (isIncoming.value && callState.value === 'ringing')
    return 'Answer on your Yeastar handset.'
  return ''
})

const callData = reactive({
  call_sid: '',
})

const contactDetails = reactive({
  full_name: '',
  number: '',
  image: '',
})

const note = ref({
  name: '',
  content: '',
})

const agentNumber = ref('')
const hangupChannelId = ref('')
const screeningChannelId = ref('')
const finishedCallIds = ref(new Set())
const boundCallId = ref('')
const dismissTimer = ref(null)
const screeningTimer = ref(null)

const isScreening = ref(false)

const errorMessage = ref('')
const callPopupWrapper = ref(null)
const callPopupHeader = ref(null)
const callPopupContainer = ref(null)
const agentAnswered = ref(false)
const hangingUp = ref(false)
const responding = ref('')
const ringtone = ref(null)

const counterUpTimer = ref(null)

const { $socket } = globalStore()
const { user: currentUser } = sessionStore()
const { width, height } = useWindowSize()

const POPUP_WIDTH = 300
const POPUP_HEIGHT = 340
const EDGE_GAP = 24

function clampX(value) {
  return Math.min(
    Math.max(EDGE_GAP, value),
    Math.max(EDGE_GAP, width.value - POPUP_WIDTH - EDGE_GAP),
  )
}

function clampY(value) {
  return Math.min(
    Math.max(EDGE_GAP, value),
    Math.max(EDGE_GAP, height.value - POPUP_HEIGHT - EDGE_GAP),
  )
}

const { x, y, style } = useDraggable(callPopupWrapper, {
  handle: callPopupHeader,
  initialValue: {
    x: clampX(width.value - POPUP_WIDTH - EDGE_GAP),
    y: clampY(height.value - POPUP_HEIGHT - EDGE_GAP),
  },
  preventDefault: true,
})

watch([width, height], () => {
  x.value = clampX(x.value)
  y.value = clampY(y.value)
})

function toggleNoteWindow() {
  showNote.value = !showNote.value
}

function saveNote() {
  createUpdateNote()
}

function createUpdateNote() {
  createResource({
    url: 'crm.integrations.api.add_note_to_call_log',
    params: {
      call_sid: callData.call_sid,
      note: note.value,
    },
    auto: true,
    onSuccess(_note) {
      note.value['name'] = _note.name
    },
  })
}

function hangUpCall() {
  if (hangingUp.value) return

  if (!hangupChannelId.value) {
    toast.error('Call not connected yet — hang up on your handset')
    direction.value = 'idle'
    return
  }

  hangingUp.value = true
  createResource({
    url: 'crm.integrations.yeastar.api.hangup_call',
    params: { channel_id: hangupChannelId.value },
    auto: true,
    onSuccess() {
      hangingUp.value = false
      clearTimeout(dismissTimer.value)
      dismissTimer.value = setTimeout(() => {
        direction.value = 'idle'
      }, HANGUP_FALLBACK_MS)
    },
    onError() {
      hangingUp.value = false
      toast.error('Error ending call')
      errorMessage.value = 'An error occurred while ending the call.'
    },
  })
}

const initiateCallResource = createResource({
  url: 'crm.integrations.yeastar.api.make_call',
  makeParams() {
    return { callee: contactDetails.number }
  },
})

function makeOutgoingCall(number) {
  closeCallPopup()
  direction.value = 'outgoing'
  contactDetails.number = number
  callState.value = 'dialing'
  callStateLabel.value = 'Dialing'

  initiateCallResource.submit(
    {},
    {
      onSuccess(data) {
        callData.call_sid = data.call_id
      },
      onError() {
        toast.error('Error initiating call')
        errorMessage.value = 'An error occurred while initiating the call.'
        direction.value = 'idle'
      },
    },
  )
}

function playAudio() {
  if (ringtone.value) return

  try {
    const context = new (window.AudioContext || window.webkitAudioContext)()
    const gain = context.createGain()
    gain.gain.value = 0.0001
    gain.connect(context.destination)

    const oscillator = context.createOscillator()
    oscillator.type = 'sine'
    oscillator.frequency.value = 440
    oscillator.connect(gain)
    oscillator.start()

    const beat = setInterval(() => {
      const now = context.currentTime
      gain.gain.setTargetAtTime(0.06, now, 0.01)
      gain.gain.setTargetAtTime(0.0001, now + 1, 0.05)
    }, 3000)

    ringtone.value = { context, oscillator, beat }
  } catch {
    ringtone.value = null
  }
}

function stopAudio() {
  if (!ringtone.value) return

  const { context, oscillator, beat } = ringtone.value
  clearInterval(beat)
  try {
    oscillator.stop()
    context.close()
  } catch {}
  ringtone.value = null
}

function setup() {
  initiateSockets()
}

function initiateSockets() {
  $socket.on('yeastar_incoming_call', (data) => {
    if (!isIdle.value && !isScreening.value) return
    closeCallPopup()
    initiateIncomingCall(data)
  })
  $socket.on('yeastar_incoming_call_resolved', (data) => {
    if (!isScreening.value || data.channel_id !== screeningChannelId.value)
      return
    if (data.resolved_by !== currentUser) closeCallPopup()
  })
  $socket.on('yeastar_call_status_changed', applyCallState)
}

function applyCallState(data) {
  if (finishedCallIds.value.has(data.call_id)) return

  if (isIdle.value) {
    if (data.is_final) return
    direction.value = data.direction === 'inbound' ? 'incoming' : 'outgoing'
  } else if (boundCallId.value && boundCallId.value !== data.call_id) {
    return
  }

  boundCallId.value = data.call_id

  isScreening.value = false
  clearTimeout(screeningTimer.value)

  callData.call_sid = data.call_id
  callState.value = data.state
  callStateLabel.value = data.label
  agentNumber.value = data.agent_number || agentNumber.value
  hangupChannelId.value = data.hangup_channel_id || hangupChannelId.value

  if (data.client_number) contactDetails.number = data.client_number
  if (data.direction)
    direction.value = data.direction === 'inbound' ? 'incoming' : 'outgoing'

  if (data.state !== 'ringing') stopAudio()

  if (data.is_final) {
    finishedCallIds.value.add(data.call_id)
    scheduleDismiss()
  }
}

function scheduleDismiss() {
  counterUpTimer.value?.stop?.()
  stopAudio()
  clearTimeout(dismissTimer.value)
  dismissTimer.value = setTimeout(() => {
    direction.value = 'idle'
  }, DISMISS_AFTER_END_MS)
}

function initiateIncomingCall(data) {
  contactDetails.number = data.caller
  screeningChannelId.value = data.channel_id
  callState.value = 'ringing'
  callStateLabel.value = 'Incoming call'
  direction.value = 'incoming'
  callData.call_sid = data.call_id
  isScreening.value = true

  playAudio()

  clearTimeout(screeningTimer.value)
  screeningTimer.value = setTimeout(
    () => {
      if (isScreening.value) closeCallPopup()
    },
    (data.hold_seconds || 10) * 1000,
  )
}

function responseToCall(action) {
  responding.value = action
  handleCallResponse(action).submit(
    {},
    {
      onSuccess() {
        responding.value = ''
        stopAudio()
        clearTimeout(screeningTimer.value)
        isScreening.value = false
        if (action === 'accept') {
          agentAnswered.value = true
          callStateLabel.value = 'Routing to your handset'
        } else {
          callState.value = 'ended'
          callStateLabel.value = 'Declined'
          finishedCallIds.value.add(callData.call_sid)
          scheduleDismiss()
        }
      },
      onError() {
        responding.value = ''
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
      return { channel_id: screeningChannelId.value, action: action }
    },
  })

function closeCallPopup() {
  clearTimeout(dismissTimer.value)
  clearTimeout(screeningTimer.value)
  initiateCallResource.reset()
  errorMessage.value = ''
  contactDetails.full_name = ''
  contactDetails.number = ''
  contactDetails.image = ''
  callState.value = ''
  callStateLabel.value = ''
  screeningChannelId.value = ''
  hangupChannelId.value = ''
  boundCallId.value = ''
  agentNumber.value = ''
  isScreening.value = false
  agentAnswered.value = false
  hangingUp.value = false
  responding.value = ''
  showNote.value = false
  note.value = { name: '', content: '' }
  callData.call_sid = ''

  counterUpTimer.value?.stop?.()
  stopAudio()
}

watch(showCallPopup, (visible) => {
  if (!visible) closeCallPopup()
})

watch(isCallActive, (active) => {
  if (active) counterUpTimer.value?.start()
})

onBeforeUnmount(() => {
  clearTimeout(dismissTimer.value)
  clearTimeout(screeningTimer.value)
  stopAudio()
  $socket.off('yeastar_incoming_call')
  $socket.off('yeastar_incoming_call_resolved')
  $socket.off('yeastar_call_status_changed')
})

defineExpose({ makeOutgoingCall, setup })
</script>
