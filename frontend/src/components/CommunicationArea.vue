<template>
  <div class="max-w-[81.7%] bg-white pl-16 p-4 pt-2 z-20">
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
          @click.stop="makeOutgoingCall"
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
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailEditor from '@/components/EmailEditor.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { usersStore } from '@/stores/users'
import { Tooltip, call } from 'frappe-ui'
import { ref, watch, computed, defineModel, onMounted } from 'vue'
import { Device } from '@twilio/voice-sdk'

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
let muted = ref(false)
let onPhone = ref(false)
let log = ref('Connecting...')
let connection = ref(null)

onMounted(() => startupClient())

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
    onPhone.value = false
    connection.value = null
    log.value = 'Logged out'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + error.message
  })

  device.on('connect', (conn) => {
    connection.value = conn
    log.value = 'Successfully established call!'
  })
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
