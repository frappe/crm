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
            class="bg-red-600 text-ink-white hover:bg-red-700"
            :tooltip="__('Hang Up')"
            size="md"
            icon="phone-off"
            @click="hangUp"
          />
          <!-- Accept incoming -->
          <Button
            v-if="callStatus == 'Incoming call'"
            class="bg-green-600 text-ink-white hover:bg-green-700"
            :tooltip="__('Accept')"
            size="md"
            icon="phone"
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

// JsSIP loaded from CDN in index.html — see Step 5
// window.JsSIP must be available

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

let ua = null          // JsSIP UserAgent
let currentSession = null  // active RTCSession

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
  if (!window.JsSIP) {
    toast.error(__('JsSIP library not loaded. Add it to index.html (see setup docs).'))
    return
  }

  if (ua) {
    ua.stop()
    ua = null
  }

  // Store host globally so makeOutgoingCall can build the SIP target URI
  window.__freepbx_host__ = creds.host

  const socket = new window.JsSIP.WebSocketInterface(creds.ws_uri)

  ua = new window.JsSIP.UA({
    sockets: [socket],
    uri: creds.sip_uri,
    password: creds.password,
    register: true,
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
  phoneNumber.value = request.from.uri.user || request.from.display_name || ''
  callStatus.value = 'Incoming call'
  showCallPopup.value = true
  showSmallCallPopup.value = false

  session.on('ended', _onCallEnded)
  session.on('failed', _onCallFailed)
  session.on('confirmed', _onCallConfirmed)
}

function acceptIncoming() {
  if (!currentSession) return
  currentSession.answer({
    mediaConstraints: { audio: true, video: false },
    pcConfig: { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] },
  })
  _attachRemoteAudio(currentSession)
}

function makeOutgoingCall(number) {
  if (!ua || !ua.isRegistered()) {
    toast.error(__('FreePBX SIP not registered yet. Please wait a moment.'))
    return
  }

  phoneNumber.value = number
  callStatus.value = 'Calling...'
  showCallPopup.value = true
  showSmallCallPopup.value = false

  const callId = _generateId()
  callData.value = { CallSid: callId }

  // Create call log via backend (non-WebRTC path for logging)
  createResource({
    url: 'crm.integrations.freepbx.handler.make_a_call',
    params: { to_number: number },
    auto: true,
    onSuccess(details) {
      callData.value = details
    },
    onError(err) {
      toast.error(err.messages?.[0] || __('Failed to create call log'))
    },
  })

  // Place the actual WebRTC call
  const session = ua.call(`sip:${number}@${_getSipDomain()}`, {
    mediaConstraints: { audio: true, video: false },
    pcConfig: { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] },
  })

  currentSession = session

  session.on('progress', () => { callStatus.value = 'Ringing...' })
  session.on('confirmed', _onCallConfirmed)
  session.on('ended', _onCallEnded)
  session.on('failed', _onCallFailed)

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
  session.connection?.addEventListener('addstream', (e) => {
    if (remoteAudio.value) {
      remoteAudio.value.srcObject = e.stream
    }
  })
  // Modern WebRTC: ontrack
  session.connection?.addEventListener('track', (e) => {
    if (remoteAudio.value && e.streams?.[0]) {
      remoteAudio.value.srcObject = e.streams[0]
    }
  })
}

function hangUp() {
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

function _getSipDomain() {
  // Extracted from the ws_uri stored during setup; fallback to hostname
  return window.__freepbx_host__ || window.location.hostname
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
