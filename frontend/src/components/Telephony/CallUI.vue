<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <FreePBXCallUI ref="freepbx" />
  <Dialog
    v-model="show"
    :options="{
      title: __('Make Call'),
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
          v-model="mobileNumber"
          type="text"
          :label="__('Mobile Number')"
        />
        <FormControl
          v-model="callMedium"
          type="select"
          :label="__('Calling Medium')"
          :options="availableMediums"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            v-model="isDefaultMedium"
            type="checkbox"
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
import FreePBXCallUI from '@/components/Telephony/FreePBXCallUI.vue'
import {
  twilioEnabled,
  exotelEnabled,
  freepbxEnabled,
  defaultCallingMedium,
} from '@/composables/settings'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const { setMakeCall } = globalStore()

const twilio = ref(null)
const exotel = ref(null)
const freepbx = ref(null)

const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')

const availableMediums = computed(() => {
  const mediums = []
  if (twilioEnabled.value) mediums.push('Twilio')
  if (exotelEnabled.value) mediums.push('Exotel')
  if (freepbxEnabled.value) mediums.push('FreePBX')
  return mediums
})

function makeCall(number) {
  const enabledCount = [twilioEnabled.value, exotelEnabled.value, freepbxEnabled.value].filter(Boolean).length
  if (enabledCount > 1 && !defaultCallingMedium.value) {
    mobileNumber.value = number
    show.value = true
    return
  }

  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value
  } else if (twilioEnabled.value) {
    callMedium.value = 'Twilio'
  } else if (exotelEnabled.value) {
    callMedium.value = 'Exotel'
  } else if (freepbxEnabled.value) {
    callMedium.value = 'FreePBX'
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
  } else if (callMedium.value === 'Exotel') {
    exotel.value.makeOutgoingCall(mobileNumber.value)
  } else if (callMedium.value === 'FreePBX') {
    freepbx.value.makeOutgoingCall(mobileNumber.value)
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
  [twilioEnabled, exotelEnabled, freepbxEnabled],
  ([twilioValue, exotelValue, freepbxValue]) =>
    nextTick(() => {
      if (twilioValue) {
        twilio.value.setup()
        callMedium.value = 'Twilio'
      }

      if (exotelValue) {
        exotel.value.setup()
        callMedium.value = 'Exotel'
      }

      if (freepbxValue) {
        freepbx.value.setup()
        callMedium.value = 'FreePBX'
      }

      if (twilioValue || exotelValue || freepbxValue) {
        setMakeCall(makeCall)
      }
    }),
  { immediate: true },
)
</script>
