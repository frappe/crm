<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Twilio Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="twilio.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="twilio.doc?.enabled && !twilio.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="twilio.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="twilio.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="twilio.doc" class="h-full">
        <div v-if="twilio.doc.enabled" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="twilio.doc.account_sid"
              :label="__('Account SID')"
              type="text"
              placeholder="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
              required
              autocomplete="off"
            />
            <Password
              v-model="twilio.doc.auth_token"
              :label="__('Auth Token')"
              placeholder="************"
              required
            />
          </div>
          <div
            v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
            class="h-px border-t border-outline-gray-modals"
          />
          <div
            v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
            class="flex items-center justify-between gap-8"
          >
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __('Twilio App Name') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('Select a Twilio App for your CRM') }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Autocomplete v-model="twilio.doc.app_name" :options="twilioApps">
                <template #footer>
                  <Button
                    :label="__('Refresh Apps')"
                    theme="gray"
                    variant="subtle"
                    class="w-full"
                    icon-left="refresh-cw"
                    :loading="twilio.fetchTwilioApps.loading"
                    @click="twilio.fetchTwilioApps.fetch"
                  />
                </template>
              </Autocomplete>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __('Record Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{
                  __('Enable call recording for incoming and outgoing calls')
                }}
              </div>
            </div>
            <div>
              <Switch v-model="twilio.doc.record_calls" size="sm" />
            </div>
          </div>
        </div>
        <!--  Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg font-medium text-ink-gray-8">
                {{ __('Twilio Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Twilio integration to make and receive calls directly from your CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="twilio.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { twilioEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { Autocomplete, Switch } from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: twilio } = useDocument(
  'CRM Twilio Settings',
  'CRM Twilio Settings',
  {
    whitelistedMethods: {
      fetchTwilioApps: {
        method: 'fetch_applications',
        onSuccess: () => twilio.reload(),
      },
    },
  },
)

const twilioApps = computed(() => {
  if (!twilio.doc?.account_sid) return []
  let comma_separated_apps = twilio.doc?.twilio_apps
  let apps = []
  if (comma_separated_apps) {
    apps = comma_separated_apps.split(',').map((app) => {
      return { label: app, value: app }
    })
  }
  return apps
})

function enable() {
  twilio.doc.enabled = true
}

function disable() {
  twilio.doc.enabled = false
  update()
}

function update() {
  twilio.save.submit(null, {
    onSuccess: () => twilio.reload(),
  })

  twilioEnabled.value = twilio.doc.enabled
}

const isDirty = computed(() => {
  return (
    twilio.doc &&
    twilio.originalDoc &&
    JSON.stringify(twilio.doc) !== JSON.stringify(twilio.originalDoc)
  )
})
</script>
