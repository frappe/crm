<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Social Planner') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Posts are published straight to your Facebook pages and their Instagram business accounts.',
          )
        }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <!-- connection -->
      <div
        class="mb-6 flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-7">
            <template v-if="connection.data?.connected">
              {{ __('Connected as {0}', [connection.data.connected_user]) }}
            </template>
            <template v-else-if="connection.data?.has_app">
              {{ __('Facebook is not connected yet') }}
            </template>
            <template v-else>
              {{ __('Set up the Meta app first') }}
            </template>
          </span>
          <span class="text-p-sm text-ink-gray-5">
            <template v-if="connection.data?.connected">
              {{ connection.data.pages }} {{ __('pages available') }}
            </template>
            <template v-else-if="connection.data?.has_app">
              {{ __('Connect to pick which pages you can publish to.') }}
            </template>
            <template v-else>
              {{ __('App ID and secret live in Settings → Meta.') }}
            </template>
          </span>
        </div>
        <Button
          v-if="connection.data?.has_app"
          :variant="connection.data?.connected ? 'outline' : 'solid'"
          :label="
            connection.data?.connected ? __('Reconnect Facebook') : __('Connect with Facebook')
          "
          @click="connectFacebook"
        />
        <Button v-else :label="__('Open Meta settings')" @click="goToMetaSettings" />
      </div>

      <!-- profiles -->
      <div class="mb-2 flex items-center justify-between gap-2">
        <span class="text-p-base-medium text-ink-gray-7">{{ __('Profiles') }}</span>
        <Button
          v-if="connection.data?.connected"
          variant="solid"
          :label="__('Import profiles')"
          iconLeft="download"
          :loading="importing"
          @click="importAccounts"
        />
      </div>
      <div
        v-if="accounts.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="account in accounts.data"
          :key="account.name"
          class="flex items-center gap-3 px-3 py-2.5"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
            :style="{ backgroundColor: platformColor(account.platform) }"
          >
            {{ platformInitial(account.platform) }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-base text-ink-gray-8">{{ account.account_name }}</div>
            <div class="truncate text-p-sm text-ink-gray-5">{{ account.platform }}</div>
          </div>
          <Switch
            :modelValue="Boolean(account.enabled)"
            size="sm"
            @update:modelValue="(v) => toggleAccount(account, v)"
          />
          <Button variant="ghost" icon="lucide-trash-2" @click="removeAccount(account)" />
        </div>
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{
          connection.data?.connected
            ? __('No profiles yet — click "Import profiles".')
            : __('Connect Facebook above to import your profiles.')
        }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import { platformColor, platformInitial } from '@/utils/social'
import { createResource, Switch, toast } from 'frappe-ui'
import { ref } from 'vue'

const importing = ref(false)

const connection = createResource({
  url: 'crm.api.social.get_connection',
  auto: true,
})

const accounts = createResource({
  url: 'crm.api.social.list_accounts_admin',
  auto: true,
})

function goToMetaSettings() {
  activeSettingsPage.value = 'Meta'
}

function connectFacebook() {
  createResource({
    url: 'crm.integrations.meta.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => (window.location.href = data.login_url),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to start login')),
  })
}

function importAccounts() {
  importing.value = true
  createResource({
    url: 'crm.api.social.import_accounts',
    auto: true,
    onSuccess: (data) => {
      importing.value = false
      accounts.reload()
      connection.reload()
      toast.success(
        __('{0} profiles imported, {1} updated', [data.created || 0, data.updated || 0]),
      )
    },
    onError: (e) => {
      importing.value = false
      toast.error(e.messages?.[0] || __('Import failed'))
    },
  })
}

function toggleAccount(account, enabled) {
  createResource({
    url: 'crm.api.social.set_account_enabled',
    params: { name: account.name, enabled },
    auto: true,
    onSuccess: () => accounts.reload(),
    onError: (e) => {
      toast.error(e.messages?.[0] || __('Failed to update'))
      accounts.reload()
    },
  })
}

function removeAccount(account) {
  createResource({
    url: 'crm.api.social.delete_account',
    params: { name: account.name },
    auto: true,
    onSuccess: () => accounts.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
