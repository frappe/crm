<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">{{ __('WhatsApp') }}</h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Connect your WhatsApp Business number: chats stay on your phone and appear here too.',
          )
        }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="status.data && !status.data.installed"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('The WhatsApp app is not installed on this site yet.') }}
      </div>

      <template v-else>
        <!-- connect -->
        <div
          class="mb-6 flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 p-4"
        >
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-7">
              {{
                status.data?.connected
                  ? __('WhatsApp is connected')
                  : __('No number connected yet')
              }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                status.data?.can_connect
                  ? __('You will scan a QR code with the WhatsApp Business app on your phone.')
                  : __('WhatsApp signup is not configured yet — ask your provider.')
              }}
            </span>
          </div>
          <Button
            :variant="status.data?.connected ? 'outline' : 'solid'"
            :disabled="!status.data?.can_connect"
            :loading="connecting"
            :label="status.data?.connected ? __('Connect another number') : __('Connect WhatsApp')"
            @click="connect"
          />
        </div>

        <!-- numbers -->
        <div v-if="status.data?.accounts?.length">
          <div class="mb-2 text-p-base-medium text-ink-gray-7">{{ __('Numbers') }}</div>
          <div class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2">
            <div
              v-for="account in status.data.accounts"
              :key="account.name"
              class="flex items-center gap-3 px-3 py-2.5"
            >
              <div class="min-w-0 flex-1">
                <div class="truncate text-p-base text-ink-gray-8">{{ account.name }}</div>
                <div class="truncate text-p-sm text-ink-gray-5">
                  {{ __('Phone number ID') }}: {{ account.phone_id }}
                </div>
              </div>
              <Badge
                v-if="account.name == status.data.default_account"
                :label="__('Sends messages')"
                theme="green"
                size="sm"
              />
              <Button
                v-else
                size="sm"
                :label="__('Use for sending')"
                @click="setDefault(account.name)"
              />
              <Button variant="ghost" icon="lucide-trash-2" @click="disconnect(account.name)" />
            </div>
          </div>
          <p class="mt-2 text-p-sm text-ink-gray-5">
            {{ __('Removing a number here does not affect the WhatsApp Business app on the phone.') }}
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

const connecting = ref(false)

const status = createResource({
  url: 'crm.integrations.whatsapp.api.get_status',
  auto: true,
})

function connect() {
  connecting.value = true
  createResource({
    url: 'crm.integrations.whatsapp.api.get_connect_url',
    auto: true,
    onSuccess: (data) => {
      connecting.value = false
      window.location.href = data.url
    },
    onError: (e) => {
      connecting.value = false
      toast.error(e.messages?.[0] || __('Could not start the connection'))
    },
  })
}

function setDefault(name) {
  createResource({
    url: 'crm.integrations.whatsapp.api.set_default_account',
    params: { name },
    auto: true,
    onSuccess: () => status.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to update')),
  })
}

function disconnect(name) {
  createResource({
    url: 'crm.integrations.whatsapp.api.disconnect',
    params: { name },
    auto: true,
    onSuccess: () => {
      toast.success(__('Number removed'))
      status.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to remove')),
  })
}
</script>
