<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('FreePBX Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="freepbx.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="freepbx.doc?.enabled && !freepbx.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="freepbx.reload()"
        />
        <Button :label="__('Disable')" variant="subtle" @click="disable" />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="freepbx.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="freepbx.doc" class="h-full">
        <div v-if="freepbx.doc.enabled" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="freepbx.doc.host"
              :label="__('FreePBX Host / IP')"
              type="text"
              placeholder="192.168.1.100"
              required
              autocomplete="off"
            />
            <FormControl
              v-model="freepbx.doc.ws_port"
              :label="__('WS Port (HTTP / plain)')"
              type="number"
              placeholder="8088"
              autocomplete="off"
            />
            <FormControl
              v-model="freepbx.doc.wss_port"
              :label="__('WSS Port (HTTPS / SSL)')"
              type="number"
              placeholder="8089"
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
                {{ __('Enable call recording for outgoing calls') }}
              </div>
            </div>
            <div>
              <Switch v-model="freepbx.doc.record_call" size="sm" />
            </div>
          </div>
          <div class="h-px border-t border-outline-gray-modals" />
        </div>
        <!-- Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg font-medium text-ink-gray-8">
                {{ __('FreePBX Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable FreePBX integration to make and receive calls directly from your CRM',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="freepbx.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { freepbxEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { Switch } from 'frappe-ui'
import { computed } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: freepbx } = useDocument(
  'CRM FreePBX Settings',
  'CRM FreePBX Settings',
)

function enable() {
  freepbx.doc.enabled = true
}

function disable() {
  freepbx.doc.enabled = false
  update()
}

function update() {
  freepbx.save.submit(null, {
    onSuccess: () => freepbx.reload(),
  })

  freepbxEnabled.value = freepbx.doc.enabled
}

const isDirty = computed(() => {
  return (
    freepbx.doc &&
    freepbx.originalDoc &&
    JSON.stringify(freepbx.doc) !== JSON.stringify(freepbx.originalDoc)
  )
})
</script>
