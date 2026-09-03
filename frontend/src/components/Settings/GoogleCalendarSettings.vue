<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Google Calendar') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Connect your calendar so bookings avoid the hours you are already busy, and appointments land in Google.',
          )
        }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        class="flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            {{
              status.data?.connected
                ? __('Your calendar is connected')
                : __('Calendar not connected')
            }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              status.data?.can_connect
                ? __('A Google window will ask you to choose the account and allow access.')
                : __('Google is not configured yet — ask your provider.')
            }}
          </span>
          <span v-if="googleError" class="text-p-sm text-ink-red-5">{{ googleError }}</span>
        </div>
        <div class="flex gap-2">
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :disabled="!status.data?.can_connect"
            :loading="connecting"
            :label="
              status.data?.connected ? __('Reconnect') : __('Connect Google Calendar')
            "
            @click="connect"
          />
          <Button
            v-if="status.data?.connected"
            variant="ghost"
            :label="__('Disconnect')"
            @click="disconnect"
          />
        </div>
      </div>

      <p v-if="status.data?.connected" class="mt-3 text-p-sm text-ink-gray-5">
        {{
          __(
            'Disconnecting only stops the sync: the appointments already created in Google stay where they are.',
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

const googleError = ref(new URLSearchParams(window.location.search).get('google_error') || '')
const connecting = ref(false)

const status = createResource({
  url: 'crm.integrations.google.api.get_status',
  auto: true,
})

function connect() {
  connecting.value = true
  createResource({
    url: 'crm.integrations.google.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => {
      connecting.value = false
      window.location.href = data.login_url
    },
    onError: (e) => {
      connecting.value = false
      toast.error(e.messages?.[0] || __('Could not start the connection'))
    },
  })
}

function disconnect() {
  createResource({
    url: 'crm.integrations.google.api.disconnect',
    auto: true,
    onSuccess: () => {
      toast.success(__('Calendar disconnected'))
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to disconnect')),
  })
}
</script>
