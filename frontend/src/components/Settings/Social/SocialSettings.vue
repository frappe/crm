<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Social Planner') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Publishing provider and connected social accounts.') }}
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
            { label: __('Manual (track only, publish yourself)'), value: 'Manual' },
            { label: 'Postiz (self-hosted)', value: 'Postiz' },
            { label: 'Ayrshare', value: 'Ayrshare' },
          ]"
        />
        <template v-if="form.provider == 'Postiz'">
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
        </template>
        <template v-else-if="form.provider == 'Ayrshare'">
          <FormControl
            v-model="form.ayrshare_api_key"
            type="password"
            :label="__('Ayrshare API key')"
            :placeholder="settings.data?.has_ayrshare_key ? __('•••••• (saved — type to replace)') : ''"
          />
        </template>
        <div>
          <Button variant="solid" :label="__('Save')" :loading="saving" @click="saveSettings" />
        </div>
      </div>

      <!-- accounts -->
      <div class="mb-2 flex items-center justify-between">
        <span class="text-p-base-medium text-ink-gray-7">{{ __('Social accounts') }}</span>
        <Button :label="__('Add account')" iconLeft="plus" @click="openAccount()" />
      </div>
      <div
        v-if="accounts.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="account in accounts.data"
          :key="account.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openAccount(account)"
        >
          <Badge :label="account.platform" theme="blue" size="sm" />
          <span class="min-w-0 flex-1 truncate text-p-base text-ink-gray-8">
            {{ account.account_name }}
          </span>
          <Badge
            :label="account.enabled ? __('Active') : __('Off')"
            :theme="account.enabled ? 'green' : 'gray'"
            size="sm"
          />
          <Button variant="ghost" icon="lucide-trash-2" @click.stop="removeAccount(account)" />
        </div>
      </div>
      <div v-else class="text-p-base text-ink-gray-5">
        {{ __('No social accounts yet.') }}
      </div>
    </div>
  </div>

  <!-- account dialog -->
  <Dialog
    v-model="showAccount"
    :options="{ title: accountForm.name ? __('Edit account') : __('Add account'), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl v-model="accountForm.account_name" type="text" :label="__('Name')" required />
        <FormControl
          v-model="accountForm.platform"
          type="select"
          :label="__('Platform')"
          :options="PLATFORMS.map((p) => ({ label: p, value: p }))"
        />
        <FormControl
          v-model="accountForm.provider_account_id"
          type="text"
          :label="__('Provider account id')"
          :description="__('Postiz integration id or Ayrshare profile key')"
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
import { createResource, Dialog, FormControl, Switch, toast } from 'frappe-ui'
import { ref, reactive } from 'vue'

const PLATFORMS = [
  'Facebook',
  'Instagram',
  'LinkedIn',
  'TikTok',
  'YouTube',
  'Pinterest',
  'Google Business Profile',
  'Threads',
  'Bluesky',
  'X',
]

const saving = ref(false)
const form = reactive({
  provider: 'Manual',
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
      toast.success(__('Account saved'))
      accounts.reload()
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
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
