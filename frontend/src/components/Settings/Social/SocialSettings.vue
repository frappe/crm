<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Social Planner') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Choose how posts get published and connect your social profiles.') }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <!-- provider -->
      <div class="mb-6 flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4">
        <FormControl
          v-model="form.provider"
          type="select"
          :label="__('Publishing provider')"
          :options="[
            {
              label: __('Meta (built-in) — Facebook & Instagram, no third party'),
              value: 'Meta',
            },
            { label: 'Postiz (self-hosted, all networks)', value: 'Postiz' },
            { label: 'Ayrshare (paid aggregator)', value: 'Ayrshare' },
            { label: __('Manual (track only, publish yourself)'), value: 'Manual' },
          ]"
        />

        <!-- Meta: reuses the Meta Lead Ads connection -->
        <template v-if="form.provider == 'Meta'">
          <div class="rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-6">
            {{
              __(
                'Publishes directly with the Meta Graph API using your connected Facebook pages and their linked Instagram business accounts. Other networks need Postiz or Ayrshare.',
              )
            }}
          </div>
          <div
            v-if="!settings.data?.meta_has_app"
            class="flex items-center justify-between gap-3"
          >
            <span class="text-p-base text-ink-gray-6">
              {{ __('First set the Meta App ID & Secret.') }}
            </span>
            <Button :label="__('Open Meta settings')" @click="goToMetaSettings" />
          </div>
          <div v-else class="flex items-center justify-between gap-3">
            <span class="text-p-base text-ink-gray-7">
              <template v-if="settings.data?.meta_connected">
                {{ __('Connected as {0}', [settings.data.meta_connected_user]) }}
                · {{ settings.data.meta_pages }} {{ __('pages') }}
              </template>
              <template v-else>{{ __('Facebook is not connected yet.') }}</template>
            </span>
            <Button
              :variant="settings.data?.meta_connected ? 'outline' : 'solid'"
              :label="
                settings.data?.meta_connected
                  ? __('Reconnect Facebook')
                  : __('Connect with Facebook')
              "
              @click="connectFacebook"
            />
          </div>
        </template>

        <template v-else-if="form.provider == 'Postiz'">
          <FormControl
            v-model="form.postiz_url"
            type="text"
            :label="__('Postiz URL')"
            :placeholder="'https://postiz.example.com'"
          />
          <FormControl
            v-model="form.postiz_api_key"
            type="password"
            :label="__('Postiz API key')"
            :placeholder="settings.data?.has_postiz_key ? __('•••••• (saved — type to replace)') : ''"
          />
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Connect new profiles in the Postiz UI, then import them here.') }}
            <a
              v-if="form.postiz_url"
              :href="form.postiz_url"
              target="_blank"
              class="text-ink-gray-7 underline"
            >
              {{ __('Open Postiz') }}
            </a>
          </div>
        </template>

        <template v-else-if="form.provider == 'Ayrshare'">
          <FormControl
            v-model="form.ayrshare_api_key"
            type="password"
            :label="__('Ayrshare API key')"
            :placeholder="settings.data?.has_ayrshare_key ? __('•••••• (saved — type to replace)') : ''"
          />
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Link networks on the Ayrshare dashboard, then import them here.') }}
            <a
              href="https://app.ayrshare.com/social-accounts"
              target="_blank"
              class="text-ink-gray-7 underline"
            >
              {{ __('Open Ayrshare') }}
            </a>
          </div>
        </template>

        <div>
          <Button variant="solid" :label="__('Save')" :loading="saving" @click="saveSettings" />
        </div>
      </div>

      <!-- accounts -->
      <div class="mb-2 flex items-center justify-between gap-2">
        <span class="text-p-base-medium text-ink-gray-7">{{ __('Social profiles') }}</span>
        <div class="flex gap-2">
          <Button
            v-if="form.provider != 'Manual'"
            variant="solid"
            :label="__('Import connected profiles')"
            iconLeft="download"
            :loading="importing"
            @click="importAccounts"
          />
          <Button :label="__('Add manually')" variant="ghost" iconLeft="plus" @click="openAccount()" />
        </div>
      </div>
      <div
        v-if="accounts.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="account in accounts.data"
          :key="account.name"
          class="flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
        >
          <span
            class="flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white"
            :style="{ backgroundColor: platformColor(account.platform) }"
          >
            {{ platformInitial(account.platform) }}
          </span>
          <div class="min-w-0 flex-1 cursor-pointer" @click="openAccount(account)">
            <div class="truncate text-p-base text-ink-gray-8">{{ account.account_name }}</div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ account.platform }}
              <template v-if="account.provider_account_id">
                · {{ account.provider_account_id }}
              </template>
            </div>
          </div>
          <Switch
            :modelValue="Boolean(account.enabled)"
            size="sm"
            @update:modelValue="(v) => toggleAccount(account, v)"
          />
          <Button variant="ghost" icon="lucide-trash-2" @click.stop="removeAccount(account)" />
        </div>
      </div>
      <div
        v-else
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{
          form.provider == 'Manual'
            ? __('No profiles yet — add them manually.')
            : __('No profiles yet — connect the provider above, then click "Import connected profiles".')
        }}
      </div>
    </div>
  </div>

  <!-- manual account dialog -->
  <Dialog
    v-model="showAccount"
    :options="{ title: accountForm.name ? __('Edit profile') : __('Add profile'), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl v-model="accountForm.account_name" type="text" :label="__('Name')" required />
        <FormControl
          v-model="accountForm.platform"
          type="select"
          :label="__('Platform')"
          :options="SOCIAL_PLATFORMS.map((p) => ({ label: p, value: p }))"
        />
        <FormControl
          v-model="accountForm.provider_account_id"
          type="text"
          :label="__('Provider account id')"
          :description="
            __('Filled automatically by the import — set it by hand only for special cases')
          "
        />
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="accountForm.enabled" size="sm" /> {{ __('Enabled') }}
        </label>
      </div>
    </template>
    <template #actions>
      <Button class="w-full" variant="solid" :label="__('Save')" @click="saveAccount" />
    </template>
  </Dialog>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import {
  SOCIAL_PLATFORMS,
  platformColor,
  platformInitial,
} from '@/utils/social'
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { ref, reactive } from 'vue'

const saving = ref(false)
const importing = ref(false)
const form = reactive({
  provider: 'Meta',
  postiz_url: '',
  postiz_api_key: '',
  ayrshare_api_key: '',
})

const settings = createResource({
  url: 'crm.api.social.get_social_settings',
  auto: true,
  onSuccess: (data) => {
    form.provider = data.provider
    form.postiz_url = data.postiz_url
  },
})

const accounts = createResource({
  url: 'crm.api.social.list_accounts_admin',
  auto: true,
})

function goToMetaSettings() {
  activeSettingsPage.value = 'Meta Lead Ads'
}

function connectFacebook() {
  createResource({
    url: 'crm.integrations.meta.oauth.get_login_url',
    auto: true,
    onSuccess: (data) => (window.location.href = data.login_url),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to start login')),
  })
}

function saveSettings() {
  saving.value = true
  createResource({
    url: 'crm.api.social.save_social_settings',
    params: { settings: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      form.postiz_api_key = ''
      form.ayrshare_api_key = ''
      toast.success(__('Settings saved'))
      settings.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}

function importAccounts() {
  importing.value = true
  createResource({
    url: 'crm.api.social.import_provider_accounts',
    auto: true,
    onSuccess: (data) => {
      importing.value = false
      accounts.reload()
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

const showAccount = ref(false)
const accountForm = reactive({
  name: null,
  account_name: '',
  platform: 'Facebook',
  provider_account_id: '',
  enabled: true,
})

function openAccount(account = null) {
  accountForm.name = account?.name || null
  accountForm.account_name = account?.account_name || ''
  accountForm.platform = account?.platform || 'Facebook'
  accountForm.provider_account_id = account?.provider_account_id || ''
  accountForm.enabled = account ? Boolean(account.enabled) : true
  showAccount.value = true
}

function saveAccount() {
  createResource({
    url: 'crm.api.social.save_account',
    params: { name: accountForm.name, account: { ...accountForm } },
    auto: true,
    onSuccess: () => {
      showAccount.value = false
      toast.success(__('Profile saved'))
      accounts.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
  })
}

function toggleAccount(account, enabled) {
  createResource({
    url: 'crm.api.social.save_account',
    params: { name: account.name, account: { ...account, enabled } },
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
