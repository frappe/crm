<template>
  <div>
    <!-- Hidden audio element for WebRTC audio output -->
    <audio ref="remoteAudio" autoplay></audio>

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
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0 cursor-pointer"
            :tooltip="__('Minimize')"
            :icon="MinimizeIcon"
            size="md"
            @click="toggleCallPopup"
          />
          <Button
            v-if="callStatus == 'Call ended' || callStatus == 'No answer'"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
            icon="x"
            size="md"
            @click="closeCallPopup"
          />
        </div>
      </div>

      <div class="body flex-1">
        <div v-if="showNote">
          <TextEditor
            ref="content"
            variant="ghost"
            editor-class="prose-sm h-[290px] text-ink-white overflow-auto mt-1"
            :bubbleMenu="true"
            :content="note.content"
            :placeholder="__('Take a note...')"
            @change="(val) => (note.content = val)"
          />
        </div>
        <TaskPanel v-else-if="showTask" ref="taskRef" :task="task" />
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
          <!-- Mute toggle -->
          <Button
            v-if="callStatus == 'In progress'"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            :tooltip="isMuted ? __('Unmute') : __('Mute')"
            size="md"
            :icon="isMuted ? MicOffIcon : MicIcon"
            @click="toggleMute"
          />
          <!-- Hang up -->
          <Button
            v-if="callStatus != 'Call ended' && callStatus != 'No answer' && callStatus != ''"
            :tooltip="__('Hang Up')"
            size="md"
            icon="phone-off"
            style="background-color: #dc2626; color: white;"
            @click="hangUp"
          />
          <!-- Accept incoming -->
          <Button
            v-if="callStatus == 'Incoming call'"
            :tooltip="__('Accept')"
            size="md"
            icon="phone"
            style="background-color: #16a34a; color: white;"
            @click="acceptIncoming"
          />
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            :tooltip="__('Add a Note')"
            size="md"
            :icon="NoteIcon"
            @click="showNoteWindow"
          />
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
            :tooltip="__('Add a Task')"
            :icon="TaskIcon"
            @click="showTaskWindow"
          />
          <Button
            v-if="contact.deal || contact.lead"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
            :iconRight="ArrowUpRightIcon"
            :label="contact.deal ? __('Deal') : __('Lead')"
            @click="openDealOrLead"
          />
        </div>

        <Button
          v-if="(note.name || task.name) && dirty"
          class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
          variant="solid"
          :label="__('Update')"
          size="md"
          @click="update"
        />
        <Button
          v-else-if="
            ((note?.content && note.content != '<p></p>') || task.title) &&
            !note.name &&
            !task.name
          "
          class="bg-surface-white !text-ink-gray-9 hover:!bg-surface-gray-3"
          variant="solid"
          :label="__('Save')"
          size="md"
          @click="save"
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
import { useDraggable, useWindowSize } from '@vueuse/core'
import { TextEditor, Avatar, Button, createResource, toast } from 'frappe-ui'
import { ref, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as JsSIP from 'jssip'

const MicIcon = 'mic'
const MicOffIcon = 'mic-off'

const remoteAudio = ref(null)
const callPopupHeader = ref(null)
const showCallPopup = ref(false)
const showSmallCallPopup = ref(false)

function toggleCallPopup() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallPopup.value = !showSmallCallPopup.value
}

const { width, height } = useWindowSize()
const { style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 250 },
  preventDefault: true,
})

// ── State ────────────────────────────────────────────────────────────────────

const callStatus = ref('')
const phoneNumber = ref('')
const callData = ref(null)
const callDuration = ref('00:00')
const isMuted = ref(false)
const counterUp = ref(null)
// Holds the latest status update if it arrives before the call log is created.
// Flushed in make_a_call's onSuccess so we never silently drop a terminal status.
const pendingStatus = ref(null)

let ua = null            // JsSIP UserAgent
let currentSession = null  // active RTCSession
let sipDomain = null     // FreePBX host IP, set when credentials are loaded
let iceServers = []      // ICE config from CRM FreePBX Settings, set when credentials are loaded

const contact = ref({ full_name: '', image: '', mobile_no: '' })

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return { phone_number: phoneNumber.value }
  },
  onSuccess(data) {
    contact.value = data
  },
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
}, { immediate: true })

// ── Note / Task ──────────────────────────────────────────────────────────────

const dirty = ref(false)
const note = ref({ name: '', content: '' })
const showNote = ref(false)
const task = ref({ name: '', title: '', description: '', assigned_to: '', due_date: '', status: 'Backlog', priority: 'Low' })
const showTask = ref(false)

function showNoteWindow() {
  showNote.value = !showNote.value
  if (!showTask.value) updateWindowHeight(showNote.value)
  if (showNote.value) showTask.value = false
}

function showTaskWindow() {
  showTask.value = !showTask.value
  if (!showNote.value) updateWindowHeight(showTask.value)
  if (showTask.value) showNote.value = false
}

function createUpdateNote() {
  createResource({
    url: 'crm.integrations.api.add_note_to_call_log',
    params: { call_sid: callData.value?.CallSid, note: note.value },
    auto: true,
    onSuccess(_note) {
      note.value.name = _note.name
      nextTick(() => { dirty.value = false })
    },
  })
}

function createUpdateTask() {
  createResource({
    url: 'crm.integrations.api.add_task_to_call_log',
    params: { call_sid: callData.value?.CallSid, task: task.value },
    auto: true,
    onSuccess(_task) {
      task.value.name = _task.name
      nextTick(() => { dirty.value = false })
    },
  })
}

watch([note, task], () => (dirty.value = true), { deep: true })

function updateWindowHeight(condition) {
  const callPopup = callPopupHeader.value.parentElement
  let top = parseInt(callPopup.style.top)
  let updatedTop = condition ? top - 224 : top + 224
  if (updatedTop < 0) updatedTop = 10
  callPopup.style.top = updatedTop + 'px'
}

function save() {
  if (note.value.content) createUpdateNote()
  if (task.value.title) createUpdateTask()
}

function update() {
  if (note.value.content) createUpdateNote()
  if (task.value.title) createUpdateTask()
}

// ── JsSIP / WebRTC ───────────────────────────────────────────────────────────

function setup() {
  // Prevent multiple registrations if setup() is called more than once
  if (ua) return

  createResource({
    url: 'crm.integrations.freepbx.handler.get_webrtc_credentials',
    auto: true,
    onSuccess(creds) {
      _initJsSIP(creds)
    },
    onError(err) {
      toast.error(err.messages?.[0] || __('Failed to load FreePBX credentials'))
    },
  })
}

function _initJsSIP(creds) {
  // Already initialized, skip
  if (ua) return

  // Store FreePBX host so makeOutgoingCall can build the correct SIP target URI
  sipDomain = creds.host
  iceServers = Array.isArray(creds.ice_servers) ? creds.ice_servers : []
  console.log('[FreePBX] SIP domain set to:', sipDomain)
  console.log('[FreePBX] ICE servers:', iceServers.map(s => s.urls))

  console.log('[FreePBX] Connecting to:', creds.ws_uri)
  console.log('[FreePBX] SIP URI:', creds.sip_uri)
  console.log('[FreePBX] Username:', creds.username)
  console.log('[FreePBX] Realm:', creds.realm)

  const socket = new JsSIP.WebSocketInterface(creds.ws_uri)

  ua = new JsSIP.UA({
    sockets: [socket],
    uri: creds.sip_uri,
    password: creds.password,
    authorization_user: creds.username,
    realm: creds.realm,
    register: true,
    connection_recovery_min_interval: 2,
    connection_recovery_max_interval: 30,
  })

  ua.on('registered', () => {
    console.log('[FreePBX] SIP registered')
  })

  ua.on('registrationFailed', (e) => {
    toast.error(__('FreePBX SIP registration failed: {0}', [e.cause]))
  })

  // Handle incoming calls
  ua.on('newRTCSession', (data) => {
    if (data.originator === 'remote') {
      _handleIncomingSession(data.session, data.request)
    }
  })

  ua.start()
}

function _handleIncomingSession(session, request) {
  currentSession = session
  // Show the caller's number (who is calling us), not our own extension
  phoneNumber.value = request.from.uri.user
    || request.from.display_name
    || request.from.uri.toString()
    || ''
  callStatus.value = 'Incoming call'
  showCallPopup.value = true
  showSmallCallPopup.value = false

  // Create a call log for the incoming call
  createResource({
    url: 'crm.integrations.freepbx.handler.make_a_call',
    params: {
      to_number: request.to.uri.user || '',
      from_number: phoneNumber.value,
      call_type: 'Incoming',
    },
    auto: true,
    onSuccess(details) {
      callData.value = details
      _flushPendingStatus()
    },
  })

  session.on('ended', (e) => {
    console.log('[FreePBX] incoming ended', e)
    const elapsed = _getElapsedSeconds()
    _onCallEnded()
    _updateCallLogStatus('completed', elapsed)
  })
  session.on('failed', (e) => {
    console.log('[FreePBX] incoming failed', e.cause)
    _onCallFailed(e)
    _updateCallLogStatus('canceled')
  })
  session.on('confirmed', (e) => {
    console.log('[FreePBX] incoming confirmed', e)
    _onCallConfirmed()
    _updateCallLogStatus('in-progress')
  })
}

function getIceServers() {
  // Configured in CRM FreePBX Settings; loaded into `iceServers` by _initJsSIP.
  // Fall back to a public STUN server so calls still work LAN-to-LAN if admin hasn't filled it in.
  return iceServers.length ? iceServers : [{ urls: 'stun:stun.l.google.com:19302' }]
}

function acceptIncoming() {
  if (!currentSession) return

  // Request microphone permission first, then answer
  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then((stream) => {
      stream.getTracks().forEach(t => t.stop()) // release — JsSIP will re-acquire
      currentSession.answer({
        mediaConstraints: { audio: true, video: false },
        pcConfig: { iceServers: getIceServers() },
      })
      _attachRemoteAudio(currentSession)
      callStatus.value = 'Connecting...'
    })
    .catch((err) => {
      console.error('[FreePBX] Microphone access denied:', err)
      toast.error(__('Microphone access denied. Please allow microphone and try again.'))
    })
}

function makeOutgoingCall(number) {
  if (!ua || !ua.isRegistered()) {
    toast.error(__('FreePBX SIP not registered yet. Please wait a moment.'))
    return
  }

  if (!sipDomain) {
    toast.error(__('FreePBX SIP domain not ready. Please refresh the page.'))
    return
  }

  console.log('[FreePBX] Calling:', `sip:${number}@${sipDomain}`)

  // Show the customer number (the number we are calling), not our extension
  phoneNumber.value = number
  callStatus.value = 'Calling...'
  showCallPopup.value = true
  showSmallCallPopup.value = false

  // Create call log in CRM (backend only logs — no AMI in WebRTC mode)
  createResource({
    url: 'crm.integrations.freepbx.handler.make_a_call',
    params: { to_number: number },
    auto: true,
    onSuccess(details) {
      callData.value = details
      _flushPendingStatus()
    },
    onError(err) {
      toast.error(err.messages?.[0] || __('Failed to create call log'))
    },
  })

  // Place the WebRTC call via JsSIP
  let session
  try {
    session = ua.call(`sip:${number}@${_getSipDomain()}`, {
      mediaConstraints: { audio: true, video: false },
      pcConfig: { iceServers: getIceServers() },
    })
    console.log('[FreePBX] Session created:', session)
  } catch (e) {
    console.error('[FreePBX] ua.call() failed:', e)
    toast.error(__('Failed to start call: {0}', [e.message]))
    callStatus.value = ''
    showCallPopup.value = false
    return
  }

  currentSession = session

  session.on('progress', (e) => {
    console.log('[FreePBX] progress', e)
    callStatus.value = 'Ringing...'
    _updateCallLogStatus('ringing')
  })
  session.on('confirmed', (e) => {
    console.log('[FreePBX] confirmed', e)
    _onCallConfirmed()
    _updateCallLogStatus('in-progress')
  })
  session.on('ended', (e) => {
    console.log('[FreePBX] ended', e)
    // Capture duration before stop() resets the timer
    const elapsed = _getElapsedSeconds()
    _onCallEnded()
    _updateCallLogStatus('completed', elapsed)
  })
  session.on('failed', (e) => {
    console.log('[FreePBX] failed', e.cause, e)
    _onCallFailed(e)
    const failStatus = e.cause === 'Rejected' || e.cause === 'Busy' ? 'busy' : 'no-answer'
    _updateCallLogStatus(failStatus)
  })

  _attachRemoteAudio(session)
}

function _onCallConfirmed() {
  counterUp.value.start()
  callStatus.value = 'In progress'
}

function _onCallEnded() {
  counterUp.value.stop()
  callDuration.value = counterUp.value.getTime(0)
  callStatus.value = 'Call ended'
  currentSession = null
}

function _onCallFailed(e) {
  counterUp.value.stop()
  callStatus.value = e.cause === 'Rejected' || e.cause === 'Busy' ? 'No answer' : 'Call ended'
  currentSession = null
}

function _attachRemoteAudio(session) {
  const wirePeerConnection = (pc) => {
    if (!pc) return

    pc.addEventListener('addstream', (e) => {
      if (remoteAudio.value) remoteAudio.value.srcObject = e.stream
    })
    pc.addEventListener('track', (e) => {
      if (remoteAudio.value && e.streams?.[0]) remoteAudio.value.srcObject = e.streams[0]
    })

    // Fallback: if ICE drops and stays dropped for >5s, force the call to end
    // even when no SIP BYE arrives (flaky WSS, NAT timeouts, etc.).
    let iceFailTimer = null
    pc.addEventListener('iceconnectionstatechange', () => {
      const state = pc.iceConnectionState
      const isDown = state === 'disconnected' || state === 'failed' || state === 'closed'
      const callActive =
        callStatus.value &&
        callStatus.value !== 'Call ended' &&
        callStatus.value !== 'No answer'

      if (isDown && callActive && !iceFailTimer) {
        iceFailTimer = setTimeout(() => {
          iceFailTimer = null
          if (callStatus.value === 'Call ended' || callStatus.value === 'No answer') return
          console.warn('[FreePBX] ICE stuck on', state, '— forcing call end')
          const elapsed = _getElapsedSeconds()
          if (currentSession) {
            try { currentSession.terminate() } catch (_) {}
            currentSession = null
          }
          _onCallEnded()
          _updateCallLogStatus('completed', elapsed)
        }, 5000)
      } else if (!isDown && iceFailTimer) {
        clearTimeout(iceFailTimer)
        iceFailTimer = null
      }
    })
  }

  if (session.connection) {
    wirePeerConnection(session.connection)
  } else {
    // RTCPeerConnection isn't created until JsSIP fires `peerconnection`
    session.on('peerconnection', (e) => wirePeerConnection(e.peerconnection))
  }
}

function hangUp() {
  const elapsed = _getElapsedSeconds()
  if (currentSession) {
    try {
      currentSession.terminate()
    } catch (_) {
      // already ended
    }
    currentSession = null
  }
  callStatus.value = 'Call ended'
  counterUp.value.stop()
  callDuration.value = counterUp.value.getTime(0)
  _updateCallLogStatus('completed', elapsed)
}

function toggleMute() {
  if (!currentSession) return
  if (isMuted.value) {
    currentSession.unmute({ audio: true })
  } else {
    currentSession.mute({ audio: true })
  }
  isMuted.value = !isMuted.value
}

function _getElapsedSeconds() {
  // Parse the displayed time string e.g. "1:23" or "1:02:45"
  if (!counterUp.value?.updatedTime) return 0
  const parts = counterUp.value.updatedTime.split(':').map(Number)
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return 0
}

function _updateCallLogStatus(status, duration = 0) {
  if (!callData.value?.CallSid) {
    // Call log creation is still in flight — remember the latest update and
    // let onSuccess flush it once CallSid is available.
    pendingStatus.value = { status, duration }
    return
  }
  createResource({
    url: 'crm.integrations.freepbx.handler.update_call_status',
    params: {
      call_sid: callData.value.CallSid,
      status,
      duration,
    },
    auto: true,
  })
}

function _flushPendingStatus() {
  if (!pendingStatus.value || !callData.value?.CallSid) return
  const { status, duration } = pendingStatus.value
  pendingStatus.value = null
  _updateCallLogStatus(status, duration)
}

function _sendHangupBeacon() {
  if (!callData.value?.CallSid) return
  if (callStatus.value === 'Call ended' || callStatus.value === 'No answer') return
  if (!navigator.sendBeacon) return
  const elapsed = _getElapsedSeconds()
  const data = new FormData()
  data.append('call_sid', callData.value.CallSid)
  data.append('status', 'completed')
  data.append('duration', String(elapsed))
  navigator.sendBeacon(
    '/api/method/crm.integrations.freepbx.handler.update_call_status',
    data,
  )
}

const _beforeUnloadHandler = () => _sendHangupBeacon()
window.addEventListener('beforeunload', _beforeUnloadHandler)

function _getSipDomain() {
  if (!sipDomain) {
    console.error('[FreePBX] SIP domain not set — credentials not loaded yet')
  }
  return sipDomain
}

function _generateId() {
  return Math.random().toString(36).substring(2, 18)
}

// ── Navigation / cleanup ─────────────────────────────────────────────────────

const router = useRouter()

function openDealOrLead() {
  if (contact.value.deal) {
    router.push({ name: 'Deal', params: { dealId: contact.value.deal } })
  } else if (contact.value.lead) {
    router.push({ name: 'Lead', params: { leadId: contact.value.lead } })
  }
}

function closeCallPopup() {
  showCallPopup.value = false
  showSmallCallPopup.value = false
  note.value = { name: '', content: '' }
  task.value = { name: '', title: '', description: '', assigned_to: '', due_date: '', status: 'Backlog', priority: 'Low' }
}

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', _beforeUnloadHandler)
  _sendHangupBeacon()
  if (ua) {
    ua.stop()
    ua = null
  }
})

defineExpose({ makeOutgoingCall, setup })
</script>

<style scoped>
@keyframes blink {
  0%   { opacity: 1; }
  50%  { opacity: 0; }
  100% { opacity: 1; }
}
.blink {
  animation: blink 1s ease-in-out 6;
}
:deep(.ProseMirror) {
  caret-color: var(--ink-white);
}
</style>
