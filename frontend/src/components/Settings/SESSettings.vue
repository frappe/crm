<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex justify-between items-start px-2">
      <div class="flex flex-col gap-1">
        <h2 class="text-2xl-semibold leading-none text-ink-gray-8">
          {{ __('AWS SES') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure AWS Simple Email Service for outbound and inbound email') }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
        <Button
          v-if="isDirty"
          variant="solid"
          :label="__('Save Changes')"
          :loading="saving"
          @click="save"
        />
      </div>
    </div>

    <div v-if="settings.loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>

    <div v-else class="flex-1 overflow-y-auto flex flex-col">

      <!-- Enable toggle -->
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7">{{ __('Enable SES Override') }}</div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Route all CRM outbound email through AWS SES instead of SMTP') }}
          </div>
        </div>
        <Switch v-model="form.enabled" size="sm" @update:modelValue="markDirty" />
      </div>

      <template v-if="form.enabled">

        <!-- Outbound -->
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Outbound') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('AWS Region') }}</label>
              <FormControl
                v-model="form.aws_region"
                type="text"
                placeholder="eu-west-1"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('Configuration Set') }}
                <span class="text-ink-gray-4 ml-1">{{ __('(optional)') }}</span>
              </label>
              <FormControl
                v-model="form.configuration_set_name"
                type="text"
                class="flex-1"
                @input="markDirty"
              />
            </div>
          </div>
        </div>

        <!-- Sender Identity -->
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Sender Identity') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-start gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0 pt-0.5">
                {{ __('Sender Mode') }}
              </label>
              <div class="flex-1 flex flex-col gap-1">
                <FormControl
                  v-model="form.sender_mode"
                  type="select"
                  :options="senderModeOptions"
                  class="w-48"
                  @update:modelValue="markDirty"
                />
                <p class="text-p-xs text-ink-gray-5">
                  <template v-if="form.sender_mode === 'user_first'">
                    {{ __('From: logged-in user when on SES-verified domain. Requires domain identity verification.') }}
                  </template>
                  <template v-else>
                    {{ __('From: always uses Default Sender Email. Safe for individual address verification.') }}
                  </template>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Default Sender Email') }}</label>
              <FormControl
                v-model="form.default_sender_email"
                type="text"
                placeholder="crm@tiberbu.app"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Default Sender Name') }}</label>
              <FormControl
                v-model="form.default_sender_name"
                type="text"
                placeholder="Tiberbu CRM"
                class="flex-1"
                @input="markDirty"
              />
            </div>
          </div>
        </div>

        <!-- Reliability -->
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Reliability') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Retry Mode') }}</label>
              <FormControl
                v-model="form.retry_mode"
                type="select"
                :options="retryModeOptions"
                class="w-40"
                @update:modelValue="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Max Attempts') }}</label>
              <FormControl
                v-model="form.total_max_attempts"
                type="number"
                class="w-24"
                @input="markDirty"
              />
            </div>
          </div>
        </div>

        <!-- AWS Credentials -->
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('AWS Credentials') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between py-1">
              <div class="flex flex-col">
                <div class="text-p-sm text-ink-gray-7">{{ __('Use Explicit Credentials') }}</div>
                <div class="text-p-xs text-ink-gray-5">
                  {{ __('Off = use EC2/ECS instance profile or environment (recommended for production)') }}
                </div>
              </div>
              <Switch
                v-model="form.use_explicit_credentials"
                size="sm"
                @update:modelValue="markDirty"
              />
            </div>
            <template v-if="form.use_explicit_credentials">
              <div class="flex items-center gap-4">
                <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Access Key ID') }}</label>
                <FormControl
                  v-model="form.access_key_id"
                  type="text"
                  class="flex-1"
                  @input="markDirty"
                />
              </div>
              <div class="flex items-center gap-4">
                <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Secret Access Key') }}</label>
                <div class="flex-1 flex flex-col gap-1">
                  <FormControl
                    v-model="form.secret_access_key"
                    type="password"
                    :placeholder="form.has_secret_access_key ? __('●●●●●● (set — enter to change)') : ''"
                    class="flex-1"
                    @input="markDirty"
                  />
                </div>
              </div>
              <div class="flex items-center gap-4">
                <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                  {{ __('Session Token') }}
                  <span class="text-ink-gray-4 ml-1">{{ __('(optional)') }}</span>
                </label>
                <FormControl
                  v-model="form.session_token"
                  type="password"
                  :placeholder="form.has_session_token ? __('●●●●●● (set — enter to change)') : ''"
                  class="flex-1"
                  @input="markDirty"
                />
              </div>
            </template>
          </div>
        </div>

        <!-- Inbound Email -->
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Inbound Email') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-start gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0 pt-0.5">
                {{ __('Email Account') }}
              </label>
              <div class="flex-1 flex flex-col gap-1">
                <FormControl
                  v-model="form.inbound_email_account"
                  type="text"
                  :placeholder="__('e.g. CRM Inbox')"
                  class="flex-1"
                  @input="markDirty"
                />
                <p class="text-p-xs text-ink-gray-5">
                  {{ __('Name of the Email Account polled for inbound replies to leads and deals.') }}
                </p>
              </div>
            </div>

            <template v-if="form.inbound_email_account">
              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Enable Incoming') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('Pull emails from this account on schedule.') }}</div>
                </div>
                <Switch v-model="form.enable_incoming" size="sm" @update:modelValue="markDirty" />
              </div>

              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Default Incoming') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('All company replies land here. Only one account can be default.') }}</div>
                </div>
                <Switch v-model="form.default_incoming" size="sm" @update:modelValue="markDirty" />
              </div>

              <div class="flex items-center gap-4">
                <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">{{ __('Append Emails To') }}</label>
                <div class="flex-1 flex flex-col gap-1">
                  <FormControl
                    v-model="form.append_to"
                    type="text"
                    placeholder="CRM Lead"
                    class="flex-1"
                    @input="markDirty"
                  />
                  <p class="text-p-xs text-ink-gray-5">
                    {{ __('DocType that inbound emails are threaded onto.') }}
                  </p>
                </div>
              </div>

              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Create Lead from Incoming Emails') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('Auto-create a lead when an email arrives from an unknown contact.') }}</div>
                </div>
                <Switch
                  v-model="form.create_lead_from_incoming_email"
                  size="sm"
                  @update:modelValue="markDirty"
                />
              </div>
            </template>
          </div>
        </div>

      </template>
    </div>

    <ErrorMessage :message="saveError" class="px-2" />
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  createResource,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { ref, reactive } from 'vue'

const saving = ref(false)
const saveError = ref('')
const isDirty = ref(false)

const form = reactive({
  enabled: false,
  aws_region: '',
  default_sender_email: '',
  default_sender_name: '',
  sender_mode: 'user_first',
  configuration_set_name: '',
  retry_mode: 'standard',
  total_max_attempts: 8,
  use_explicit_credentials: false,
  access_key_id: '',
  secret_access_key: '',
  session_token: '',
  has_secret_access_key: false,
  has_session_token: false,
  inbound_email_account: '',
  enable_incoming: false,
  default_incoming: false,
  append_to: 'CRM Lead',
  create_lead_from_incoming_email: false,
})

const senderModeOptions = [
  { label: __('User first (recommended)'), value: 'user_first' },
  { label: __('Static'), value: 'static' },
]

const retryModeOptions = [
  { label: __('Standard'), value: 'standard' },
  { label: __('Adaptive'), value: 'adaptive' },
  { label: __('Legacy'), value: 'legacy' },
]

const settings = createResource({
  url: 'crm.api.ses.get_settings',
  auto: true,
  onSuccess(data) {
    Object.assign(form, data)
    // passwords come back as booleans (has_secret_access_key); clear the input fields
    form.secret_access_key = ''
    form.session_token = ''
    isDirty.value = false
  },
})

function markDirty() {
  isDirty.value = true
  saveError.value = ''
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    const payload = { ...form }
    // Never send the boolean sentinel fields back
    delete payload.has_secret_access_key
    delete payload.has_session_token
    // Empty password fields mean "don't change" — strip them out
    if (!payload.secret_access_key) delete payload.secret_access_key
    if (!payload.session_token) delete payload.session_token

    const result = await createResource({
      url: 'crm.api.ses.update_settings',
      method: 'POST',
    }).submit({ settings: payload })

    if (result) {
      Object.assign(form, result)
      form.secret_access_key = ''
      form.session_token = ''
    }
    isDirty.value = false
    toast.success(__('SES settings saved'))
  } catch (err) {
    saveError.value = err?.message || __('Failed to save settings')
  } finally {
    saving.value = false
  }
}
</script>
