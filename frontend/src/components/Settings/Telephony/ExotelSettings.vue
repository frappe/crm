<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Exotel Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="exotel.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="exotel.doc?.enabled && !exotel.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="exotel.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="exotel.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="exotel.doc" class="h-full">
        <div v-if="exotel.doc.enabled" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="exotel.doc.api_key"
              :label="__('API Key')"
              type="text"
              placeholder="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
              required
              autocomplete="off"
            />
            <Password
              v-model="exotel.doc.api_token"
              :label="__('API Token')"
              placeholder="************"
              required
            />
            <FormControl
              v-model="exotel.doc.account_sid"
              :label="__('Account SID')"
              type="text"
              placeholder="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
              required
              autocomplete="off"
            />
            <FormControl
              v-model="exotel.doc.webhook_verify_token"
              :label="__('Webhook Verify Token')"
              type="text"
              placeholder="my_secure_token_123"
              required
              autocomplete="off"
            />
            <FormControl
              v-model="exotel.doc.subdomain"
              :label="__('Subdomain')"
              type="text"
              placeholder="api.exotel.com"
              required
              autocomplete="off"
            />
          </div>
          <div class="h-px border-t border-outline-gray-modals" />
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
              <Switch v-model="exotel.doc.record_call" size="sm" />
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
                {{ __('Exotel Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Exotel integration to make and receive calls directly from your CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="exotel.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { exotelEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { Switch } from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: exotel } = useDocument(
  'CRM Exotel Settings',
  'CRM Exotel Settings',
)

function enable() {
  exotel.doc.enabled = true
}

function disable() {
  exotel.doc.enabled = false
  update()
}

function update() {
  exotel.save.submit(null, {
    onSuccess: () => exotel.reload(),
  })

  exotelEnabled.value = exotel.doc.enabled
}

const isDirty = computed(() => {
  return (
    exotel.doc &&
    exotel.originalDoc &&
    JSON.stringify(exotel.doc) !== JSON.stringify(exotel.originalDoc)
  )
})
</script>
