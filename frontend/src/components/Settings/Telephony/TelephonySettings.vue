<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8">
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1 w-9/12">
        <h2
          class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-8"
        >
          {{ __('Telephony Settings') }}
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure Telephony Settings for your CRM') }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          v-if="isDirty"
          :loading="
            isNewDoc ? insertResource.loading : telephonyAgent.save?.loading
          "
          :label="__('Update')"
          variant="solid"
          @click="update"
        />
      </div>
    </div>

    <div v-if="telephonyAgent.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-8 py-3 pl-2 pr-1">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default Medium') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Default Calling Medium for Logged In User') }}
          </div>
        </div>
        <div class="flex items-center gap-1">
          <FormControl
            v-model="telephonyAgent.doc.default_medium"
            type="select"
            class="w-44 p-1"
            :options="[
              { label: __(''), value: '' },
              { label: __('Twilio'), value: 'Twilio' },
              { label: __('Exotel'), value: 'Exotel' },
            ]"
            :placeholder="__('Select Medium')"
          />
          <Button
            v-if="telephonyAgent.doc.default_medium"
            icon="x"
            :tooltip="__('Clear')"
            @click="telephonyAgent.doc.default_medium = ''"
          />
        </div>
      </div>
      <div
        v-if="twilioEnabled"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />
      <div
        v-if="twilioEnabled"
        class="flex items-center justify-between gap-8 py-3 pl-2 pr-1"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Twilio Number') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Set the Twilio number to be used for outgoing calls.') }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.twilio_number"
            class="flex-1 truncate w-44 p-1"
            :placeholder="__('Enter Twilio Number')"
            placement="bottom-end"
          />
        </div>
      </div>
      <div
        v-if="exotelEnabled"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />
      <div
        v-if="exotelEnabled"
        class="flex items-center justify-between gap-8 py-3 pl-2 pr-1"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Exotel Number') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Set the Exotel number to be used for outgoing calls.') }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.exotel_number"
            class="flex-1 truncate w-44 p-1"
            :placeholder="__('Enter Exotel Number')"
            placement="bottom-end"
          />
        </div>
      </div>
      <div
        v-if="exotelEnabled"
        class="flex items-center justify-between gap-8 py-3 pl-2 pr-1"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Personal Mobile No.') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Enter your personal mobile number used by Exotel to make calls',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.mobile_no"
            class="flex-1 truncate w-44 p-1"
            :placeholder="__('Enter Personal Mobile No.')"
            placement="bottom-end"
          />
        </div>
      </div>

      <div
        v-if="isManager()"
        class="flex items-center justify-between text-lg text-ink-gray-8 font-semibold mt-4 py-3 px-2"
      >
        {{ __('Integrations') }}
      </div>

      <div
        v-if="isManager()"
        class="flex items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('Twilio') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __('Configure your Twilio Telephony Integration Settings here')
            }}
          </span>
        </div>
        <Button
          :label="__('Configure')"
          @click="emit('updateStep', 'twilio-settings')"
        />
      </div>

      <div
        v-if="isManager()"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />

      <div
        v-if="isManager()"
        class="flex items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('Exotel') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __('Configure your Exotel Telephony Integration Settings here')
            }}
          </span>
        </div>
        <Button
          :label="__('Configure')"
          @click="emit('updateStep', 'exotel-settings')"
        />
      </div>
    </div>
    <ErrorMessage
      :message="isNewDoc ? insertResource.error : telephonyAgent.save?.error"
    />
  </div>
</template>
<script setup>
import {
  FormControl,
  Badge,
  ErrorMessage,
  FeatherIcon,
  createResource,
  toast,
} from 'frappe-ui'
import { twilioEnabled, exotelEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { ref, computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { getUser, isManager } = usersStore()

const isNewDoc = ref(false)

const { document: telephonyAgent } = useDocument(
  'CRM Telephony Agent',
  getUser().name,
  {
    onError: (err) => {
      if (err.exc_type === 'DoesNotExistError') {
        isNewDoc.value = true
        telephonyAgent.doc = {}
        telephonyAgent.originalDoc = {}
      }
    },
  },
)

const insertResource = createResource({
  url: 'frappe.client.insert',
  onSuccess: (data) => {
    isNewDoc.value = false
    telephonyAgent.doc = data
    telephonyAgent.originalDoc = JSON.parse(JSON.stringify(data))
    toast.success(__('Document created successfully'))
  },
  onError: (err) => {
    err.messages?.forEach((msg) => toast.error(msg))
  },
})

function update() {
  if (!isDirty.value) return

  if (isNewDoc.value) {
    insertResource.submit({
      doc: {
        doctype: 'CRM Telephony Agent',
        user: getUser().name,
        ...telephonyAgent.doc,
      },
    })
  } else {
    telephonyAgent.save.submit()
  }
}

const isDirty = computed(() => {
  return (
    telephonyAgent.doc &&
    telephonyAgent.originalDoc &&
    JSON.stringify(telephonyAgent.doc) !==
      JSON.stringify(telephonyAgent.originalDoc)
  )
})
</script>
