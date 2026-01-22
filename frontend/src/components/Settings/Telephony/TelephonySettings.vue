<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8">
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1 w-9/12">
        <h2
          class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-8"
        >
          {{ __('Telephony settings') }}
          <Badge
            v-if="mediumChanged"
            :label="__('Not saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure telephony settings for your CRM') }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :loading="updateMediumResource.isLoading"
          :disabled="!mediumChanged"
          :label="__('Update')"
          variant="solid"
          @click="update"
        />
      </div>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <!-- General -->
      <div class="flex items-center justify-between gap-8 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default medium') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Default calling medium for logged in user') }}
          </div>
        </div>
        <div class="flex items-center gap-1">
          <FormControl
            type="select"
            class="w-40"
            :options="[
              { label: __(''), value: '' },
              { label: __('Twilio'), value: 'Twilio' },
              { label: __('Exotel'), value: 'Exotel' },
            ]"
            v-model="defaultCallingMedium"
            :placeholder="__('Select medium')"
          />
          <Button
            v-if="defaultCallingMedium"
            icon="x"
            :tooltip="__('Clear')"
            @click="defaultCallingMedium = ''"
          />
        </div>
      </div>

      <div
        v-if="isManager()"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />

      <div
        v-if="isManager()"
        class="flex items-center justify-between py-3 px-2 cursor-pointer hover:bg-gray-50 rounded"
        @click="emit('updateStep', 'twilio-settings')"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Twilio') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __('Configure your twilio telephony integration settings here')
            }}
          </div>
        </div>
        <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
      </div>

      <div
        v-if="isManager()"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />

      <div
        v-if="isManager()"
        class="flex items-center justify-between py-3 px-2 cursor-pointer hover:bg-gray-50 rounded"
        @click="emit('updateStep', 'exotel-settings')"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Exotel') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __('Configure your exotel telephony integration settings here')
            }}
          </div>
        </div>
        <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
      </div>
    </div>
    <ErrorMessage :message="error" />
  </div>
</template>
<script setup>
import {
  FormControl,
  Badge,
  ErrorMessage,
  FeatherIcon,
  createResource,
} from 'frappe-ui'
import {
  defaultCallingMedium,
  twilioEnabled,
  exotelEnabled,
} from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { toast } from 'frappe-ui'
import { ref, watch } from 'vue'

const emit = defineEmits(['updateStep'])

const { isManager, isTelephonyAgent } = usersStore()

const mediumChanged = ref(false)

watch(defaultCallingMedium, () => {
  mediumChanged.value = true
})

function update() {
  if (!validateIfDefaultMediumIsEnabled()) return
  if (mediumChanged.value) {
    updateMediumResource.submit()
  }
}

const updateMediumResource = createResource({
  url: 'crm.integrations.api.set_default_calling_medium',
  makeParams: () => ({
    medium: defaultCallingMedium.value,
  }),
  onSuccess: () => {
    mediumChanged.value = false
    error.value = ''
    toast.success(__('Default calling medium updated successfully'))
  },
  onError: (err) => {
    error.value = err.message
  },
})

const error = ref('')

function validateIfDefaultMediumIsEnabled() {
  if (isTelephonyAgent() && !isManager()) return true

  if (defaultCallingMedium.value === 'Twilio' && !twilioEnabled.value) {
    error.value = __('Twilio is not enabled')
    return false
  }
  if (defaultCallingMedium.value === 'Exotel' && !exotelEnabled.value) {
    error.value = __('Exotel is not enabled')
    return false
  }
  return true
}
</script>
