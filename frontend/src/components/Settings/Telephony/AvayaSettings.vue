<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Avaya Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="avaya.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="avaya.doc?.enabled && !avaya.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="avaya.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="avaya.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="avaya.doc" class="h-full">
        <div v-if="avaya.doc.enabled" class="space-y-4">
          <!-- Mode + common fields -->
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="avaya.doc.mode"
              :label="__('Mode')"
              type="select"
              :options="[
                { label: __('Cloud (AXP)'), value: 'Cloud (AXP)' },
                { label: __('On-Prem (Aura/AES)'), value: 'On-Prem (Aura/AES)' },
              ]"
              required
            />
            <Password
              v-model="avaya.doc.webhook_verify_token"
              :label="__('Webhook Verify Token')"
              placeholder="************"
              required
            />
            <FormControl
              v-model="avaya.doc.connector_endpoint"
              :label="__('Connector Endpoint')"
              type="text"
              :placeholder="__('https://connector.example.com')"
              autocomplete="off"
            />
          </div>

          <!-- Cloud (AXP) fields -->
          <template v-if="avaya.doc.mode === 'Cloud (AXP)'">
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Cloud (AXP)') }}
            </div>
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="avaya.doc.axp_base_url"
                :label="__('AXP Base URL')"
                type="text"
                placeholder="https://api.avayacloud.com"
                required
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.axp_region"
                :label="__('AXP Region')"
                type="text"
                placeholder="us-east-1"
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.account_id"
                :label="__('Account ID')"
                type="text"
                placeholder="ACXXXXXXXXXXXXXXXX"
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.client_id"
                :label="__('Client ID')"
                type="text"
                placeholder="ACXXXXXXXXXXXXXXXX"
                required
                autocomplete="off"
              />
              <Password
                v-model="avaya.doc.client_secret"
                :label="__('Client Secret')"
                placeholder="************"
                required
              />
            </div>
          </template>

          <!-- On-Prem (Aura/AES) fields -->
          <template v-else-if="avaya.doc.mode === 'On-Prem (Aura/AES)'">
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('On-Prem (Aura/AES)') }}
            </div>
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="avaya.doc.aes_host"
                :label="__('AES Host')"
                type="text"
                placeholder="aes.example.com"
                required
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.cm_id"
                :label="__('Communication Manager ID')"
                type="text"
                placeholder="CM1"
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.cti_user"
                :label="__('CTI User')"
                type="text"
                placeholder="ctiuser"
                required
                autocomplete="off"
              />
              <Password
                v-model="avaya.doc.cti_password"
                :label="__('CTI Password')"
                placeholder="************"
                required
              />
              <FormControl
                v-model="avaya.doc.dmcc_or_tsapi_link"
                :label="__('DMCC / TSAPI Link')"
                type="text"
                placeholder="dmcc_link1"
                autocomplete="off"
              />
              <FormControl
                v-model="avaya.doc.recorder_base_url"
                :label="__('Recorder Base URL')"
                type="text"
                placeholder="https://recorder.example.com"
                autocomplete="off"
              />
              <Password
                v-model="avaya.doc.recorder_auth"
                :label="__('Recorder Auth')"
                placeholder="************"
              />
            </div>
          </template>

          <div class="h-px border-t border-outline-elevation-2" />
          <div class="flex items-center justify-between">
            <div class="flex flex-col">
              <div class="text-p-base-medium text-ink-gray-7 truncate">
                {{ __('Record Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{ __('Enable call recording for incoming and outgoing calls') }}
              </div>
            </div>
            <div>
              <Switch v-model="avaya.doc.record_calls" size="sm" />
            </div>
          </div>
        </div>

        <!-- Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg-medium text-ink-gray-8">
                {{ __('Avaya Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Avaya integration to make and receive calls directly from your CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="avaya.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { setEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { Switch } from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: avaya } = useDocument(
  'CRM Avaya Settings',
  'CRM Avaya Settings',
)

function enable() {
  avaya.doc.enabled = true
}

function disable() {
  avaya.doc.enabled = false
  update()
}

function update() {
  avaya.save.submit(null, {
    onSuccess: () => avaya.reload(),
  })

  setEnabled('avaya', avaya.doc.enabled)
}

const isDirty = computed(() => {
  return (
    avaya.doc &&
    avaya.originalDoc &&
    JSON.stringify(avaya.doc) !== JSON.stringify(avaya.originalDoc)
  )
})
</script>
