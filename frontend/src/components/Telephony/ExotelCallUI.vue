<template>
  <div>
    <div
      v-show="showSmallCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-2 rounded-full bg-surface-gray-7 px-1.5 py-[7px] text-base text-ink-gray-2"
      @click="toggleCallPopup"
    >
      <div
        class="flex justify-center items-center size-5 rounded-full bg-surface-gray-6"
      >
        <Avatar
          v-if="contact.image"
          :image="contact.image"
          :label="contact.full_name"
          class="size-3"
        />
        <AvatarIcon v-else class="size-3" />
      </div>
      <div class="text-base font-medium">
        <span class="">{{ phoneNumber }}</span>
        <span class="font-normal text-ink-gray-4"> · </span>
        <span
          v-if="callStatus == 'In Progress'"
          class="font-normal text-ink-gray-4"
        >
          00:38
        </span>
        <span v-else class="font-normal text-ink-gray-4">{{ callStatus }}</span>
      </div>
      <Button
        variant="solid"
        theme="red"
        class="text-white !size-5 rounded-full"
        @click="endCall"
      >
        <template #icon>
          <PhoneIcon class="w-3 h-3 rotate-[135deg]" />
        </template>
      </Button>
    </div>
    <Dialog
      v-model="showCallModal"
      :options="{
        title: 'Make a call',
        actions: [
          {
            label: 'Make a Call',
            variant: 'solid',
            onClick: makeCall,
          },
        ],
      }"
    >
      <template #body-content>
        <div>
          <FormControl
            v-model="phoneNumber"
            label="Phone Number"
            placeholder="+917666980887"
          />
        </div>
      </template>
    </Dialog>

    <div
      v-show="showCallPopup"
      ref="callPopup"
      class="fixed z-20 w-[280px] min-h-44 flex gap-2 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 pt-2.5 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <!-- <pre>{{ callData }}</pre> -->
      <div class="header flex items-center justify-between gap-2 text-base">
        <div v-if="callStatus == 'In Progress'">00:38</div>
        <div v-else>{{ __(callStatus) }}</div>
        <Button
          @click="toggleCallPopup"
          class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6"
          size="md"
        >
          <template #icon>
            <MinimizeIcon class="h-4 w-4 cursor-pointer" />
          </template>
        </Button>
      </div>
      <div class="body flex-1">
        <div v-if="showNote" class="h-[294px] text-base">{{ note }}</div>
        <div v-else class="flex items-center gap-3">
          <Avatar
            v-if="contact.image"
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
          <div v-if="contact.full_name" class="flex flex-col gap-1.5">
            <div class="text-lg font-medium">{{ contact.full_name }}</div>
            <div class="text-base text-ink-gray-6">{{ phoneNumber }}</div>
          </div>
          <div v-else class="text-lg font-medium">{{ phoneNumber }}</div>
        </div>
      </div>
      <div class="footer flex justify-between gap-2">
        <div class="flex gap-2">
          <Button
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            :icon="mute ? 'mic-off' : 'mic'"
            size="md"
            @click="toggleMute"
          />
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
            :icon="'more-horizontal'"
            class="bg-surface-gray-6 text-ink-white hover:bg-surface-gray-5"
            size="md"
          />
        </div>
        <Button
          variant="solid"
          theme="red"
          class="text-white"
          size="md"
          @click="endCall"
        >
          <template #icon>
            <PhoneIcon class="w-4 h-4 rotate-[135deg]" />
          </template>
        </Button>
      </div>
    </div>
  </div>
</template>
<script setup>
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { Button, Dialog, FormControl, call, Avatar } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { ref, onBeforeUnmount, onMounted } from 'vue'

const { getContact, getLeadContact } = contactsStore()
const { $socket, setMakeCall } = globalStore()

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

const showCallModal = ref(false)
const callStatus = ref('')
const phoneNumber = ref('09821259504')
const callData = ref(null)

const contact = ref({
  full_name: '',
  mobile_no: '',
})

const mute = ref(false)

function toggleMute() {
  mute.value = !mute.value
}

const note = ref(
  'This is a note for the call. This is a note for the call. This is a note for the call. This is a note for the call.',
)

const showNote = ref(false)

function showNoteWindow() {
  showNote.value = !showNote.value

  let top = parseInt(callPopup.value.style.top)
  let updatedTop = 0

  updatedTop = showNote.value ? top - 224 : top + 224

  if (updatedTop < 0) {
    updatedTop = 10
  }

  callPopup.value.style.top = updatedTop + 'px'
}

function showMakeCallModal(number) {
  showCallModal.value = true
  phoneNumber.value = number
}

function makeCall() {
  contact.value = getContact(phoneNumber.value)
  if (!contact.value) {
    contact.value = getLeadContact(phoneNumber.value)
  }

  showCallModal.value = false
  callStatus.value = 'Calling...'
  showCallPopup.value = true

  call('crm.integrations.exotel.handler.make_a_call', {
    to_number: phoneNumber.value,
    from_number: '07666980887',
    caller_id: '08047091710',
  })
}

function endCall() {
  callStatus.value = ''
  showCallPopup.value = false
  showSmallCallPopup.value = false
  note.value = ''
}

onBeforeUnmount(() => {
  $socket.off('exotel_call')
})

onMounted(() => {
  $socket.on('exotel_call', (data) => {
    callData.value = data
    console.log(data)

    if (
      data.EventType == 'answered' &&
      data.Direction == 'outbound-api' &&
      data.Status == 'in-progress' &&
      data['Legs[0][Status]'] == 'in-progress' &&
      data['Legs[1][Status]'] == ''
    ) {
      callStatus.value = 'Ringing...'
    } else if (
      data.EventType == 'answered' &&
      data.Direction == 'outbound-api' &&
      data.Status == 'in-progress' &&
      data['Legs[1][Status]'] == 'in-progress'
    ) {
      callStatus.value = 'In Progress'
    } else if (
      data.EventType == 'terminal' &&
      data.Direction == 'outbound-api' &&
      (data.Status == 'completed' || data.Status == 'no-answer')
    ) {
      callStatus.value = 'Call Ended'
    }

    if (
      data.EventType == 'Dial' &&
      data.Direction == 'incoming' &&
      data.Status == 'busy'
    ) {
      callStatus.value = 'Incoming Call'
    } else if (
      data.EventType == 'Terminal' &&
      data.Direction == 'incoming' &&
      data.Status == 'free'
    ) {
      callStatus.value = 'Call Ended'
    }

    if (!showCallPopup.value && !showSmallCallPopup.value) {
      showCallPopup.value = true
    }

    if (callStatus.value == 'Call Ended') {
      setTimeout(() => {
        showCallPopup.value = false
        showSmallCallPopup.value = false
        note.value = ''
      }, 2000)
    }
  })

  setMakeCall(showMakeCallModal)
})
</script>
