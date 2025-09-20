<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <RingCentralCallUI ref = "ringcentral" />

  <Dialog
    v-model="show"
    :options="{
      title: __('Make call'),
      actions: [
        {
          label: __('Call using {0}', [callMedium]),
          variant: 'solid',
          onClick: makeCallUsing,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="text"
          v-model="mobileNumber"
          :label="__('Mobile Number')"
        />
        <FormControl
          type="select"
          v-model="callMedium"
          :label="__('Calling Medium')"
          :options="['Twilio', 'Exotel','RingCentral']"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            type="checkbox"
            v-model="isDefaultMedium"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __('You can change the default calling medium from the settings')
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import TwilioCallUI from '@/components/Telephony/TwilioCallUI.vue'
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import RingCentralCallUI from '@/components/Telephony/RingCentralCallUI.vue'
import {
  twilioEnabled,
  exotelEnabled,
  ringcentralEnabled,
  defaultCallingMedium,
} from '@/composables/settings'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { nextTick, ref, watch } from 'vue'

const { setMakeCall } = globalStore()

const twilio = ref(null)
const exotel = ref(null)
const ringcentral = ref(null)
const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')

function makeCall(number) {
  if (
    twilioEnabled.value &&
    exotelEnabled.value &&
    ringcentralEnabled.value &&
    !defaultCallingMedium.value
  ) {
    mobileNumber.value = number
    show.value = true
    return
  }

  if (twilioEnabled.value) {
    callMedium.value = 'Twilio'
  } else if (exotelEnabled.value) {
    callMedium.value = 'Exotel'
  } else {
    callMedium.value = 'RingCentral'
  }

  mobileNumber.value = number
  makeCallUsing()
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium()
  }

  if (callMedium.value === 'Twilio') {
    twilio.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'Exotel') {
    exotel.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'RingCentral') {
    ringcentral.value.makeOutgoingCall(mobileNumber.value)
  }
  show.value = false
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

watch(
  [twilioEnabled, exotelEnabled, ringcentralEnabled],
  ([twilioValue, exotelValue, ringcentralValue]) =>
    nextTick(() => {
      if (twilioValue) {
        twilio.value.setup()
        callMedium.value = 'Twilio'
      }

      if (exotelValue) {
        exotel.value.setup()
        callMedium.value = 'Exotel'
      }

      if (ringcentralValue) {
        ringcentral.value.setup()
        callMedium.value = 'RingCentral'
      }

      if (twilioValue || exotelValue || ringcentralValue) {
        callMedium.value = 'Twilio'
        setMakeCall(makeCall)
      }
    }),
  { immediate: true },
)
</script>
