<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex justify-between items-start px-2">
      <div class="flex flex-col gap-1">
        <h2 class="text-2xl-semibold leading-none text-ink-gray-8">
          {{ __('AWS SES') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure AWS Simple Email Service for outbound email delivery') }}
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
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Enable SES Override') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Route all CRM outbound email through AWS SES instead of SMTP') }}
          </div>
        </div>
        <Switch
          v-model="form.enabled"
          size="sm"
          @update:modelValue="markDirty"
        />
      </div>

      <template v-if="form.enabled">
        <div class="h-px border-t mx-2 border-outline-elevation-2" />

        <!-- AWS Configuration -->
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('AWS Configuration') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('AWS Region') }}
              </label>
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

        <div class="h-px border-t mx-2 border-outline-elevation-2" />

        <!-- Sender Identity -->
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
                    {{ __('From: always uses Default Sender Email below. Safe for individual address verification.') }}
                  </template>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('Default Sender Email') }}
              </label>
              <FormControl
                v-model="form.default_sender_email"
                type="text"
                placeholder="crm@tiberbu.app"
                class="flex-1"
                @input="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('Default Sender Name') }}
              </label>
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

        <div class="h-px border-t mx-2 border-outline-elevation-2" />

        <!-- Reliability -->
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Reliability') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('Retry Mode') }}
              </label>
              <FormControl
                v-model="form.retry_mode"
                type="select"
                :options="retryModeOptions"
                class="w-40"
                @update:modelValue="markDirty"
              />
            </div>
            <div class="flex items-center gap-4">
              <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                {{ __('Max Attempts') }}
              </label>
              <FormControl
                v-model="form.total_max_attempts"
                type="number"
                class="w-24"
                @input="markDirty"
              />
            </div>
          </div>
        </div>

        <div class="h-px border-t mx-2 border-outline-elevation-2" />

        <!-- Inbound -->
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Inbound Email') }}
          </div>
          <div class="flex flex-col gap-3">
            <!-- Account name -->
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
                  {{ __('Name of the Email Account used to poll for inbound replies to leads and deals.') }}
                </p>
              </div>
            </div>

            <template v-if="form.inbound_email_account">
              <!-- Enable Incoming -->
              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Enable Incoming') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('Pull emails from this account on schedule.') }}</div>
                </div>
                <Switch
                  v-model="form.enable_incoming"
                  size="sm"
                  @update:modelValue="markDirty"
                />
              </div>

              <!-- Default Incoming -->
              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Default Incoming') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('All replies to the company address land here. Only one account can be default.') }}</div>
                </div>
                <Switch
                  v-model="form.default_incoming"
                  size="sm"
                  @update:modelValue="markDirty"
                />
              </div>

              <!-- Append To -->
              <div class="flex items-center gap-4">
                <label class="text-p-sm text-ink-gray-7 w-44 shrink-0">
                  {{ __('Append Emails To') }}
                </label>
                <div class="flex-1 flex flex-col gap-1">
                  <FormControl
                    v-model="form.append_to"
                    type="text"
                    placeholder="CRM Lead"
                    class="flex-1"
                    @input="markDirty"
                  />
                  <p class="text-p-xs text-ink-gray-5">
                    {{ __('DocType that inbound emails are threaded onto. Set to "CRM Lead" to link replies to lead records.') }}
                  </p>
                </div>
              </div>

              <!-- Create Lead -->
              <div class="flex items-center justify-between py-1">
                <div class="flex flex-col">
                  <div class="text-p-sm text-ink-gray-7">{{ __('Create Lead from Incoming Emails') }}</div>
                  <div class="text-p-xs text-ink-gray-5">{{ __('Automatically create a lead when an email arrives from an unknown contact.') }}</div>
                </div>
                <Switch
                  v-model="form.create_lead_from_incoming_email"
                  size="sm"
                  @update:modelValue="markDirty"
                />
              </div>
            </template>

            <p class="text-p-xs text-ink-gray-4">
              {{ __('To configure IMAP credentials for this account, go to') }}
              <a
                href="/app/email-account"
                target="_blank"
                class="text-ink-blue-6 underline underline-offset-2"
              >{{ __('Email Accounts') }} ↗</a>
            </p>
          </div>
        </div>

        <div class="h-px border-t mx-2 border-outline-elevation-2" />

        <!-- Credentials -->
        <div class="px-2 pt-4 pb-2">
          <div class="text-xs-medium text-ink-gray-5 uppercase tracking-wider mb-3">
            {{ __('Credentials') }}
          </div>
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between py-1">
              <div class="flex flex-col">
                <div class="text-p-sm text-ink-gray-7">
                  {{ __('Use Explicit Credentials') }}
                </div>
                <div class="text-p-xs text-ink-gray-5">
                  {{ __('When off, the EC2/ECS instance profile or default provider chain is used (recommended for production)') }}
                </div>
              </div>
              <Switch
                v-model="form.use_explicit_credentials"
                size="sm"
                @update:modelValue="markDirty"
              />
            </div>
            <div class="flex items-center gap-2 text-p-sm text-ink-gray-5">
              <span
                :class="form.has_access_key && form.use_explicit_credentials ? 'text-ink-blue-6' : 'text-ink-gray-4'"
              >
                {{ form.has_access_key && form.use_explicit_credentials ? '●' : '○' }}
              </span>
              <span>
                {{
                  form.has_access_key && form.use_explicit_credentials
                    ? __('Secret key configured')
                    : __('No secret key — using instance profile')
                }}
              </span>
              <a
                href="/app/aws-ses-settings"
                target="_blank"
                class="ml-2 text-ink-blue-6 underline underline-offset-2"
              >
                {{ __('Manage secrets in Desk') }} ↗
              </a>
            </div>
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
import { ref, reactive, computed, watch } from 'vue'

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
  has_access_key: false,
  inbound_email_account: '',
  enable_incoming: false,
  default_incoming: false,
  append_to: '',
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
    delete payload.has_access_key
    const result = await createResource({
      url: 'crm.api.ses.update_settings',
      method: 'POST',
    }).submit({ settings: payload })
    if (result) Object.assign(form, result)
    isDirty.value = false
    toast.success(__('SES settings saved'))
  } catch (err) {
    saveError.value = err?.message || __('Failed to save settings')
  } finally {
    saving.value = false
  }
}
</script>
