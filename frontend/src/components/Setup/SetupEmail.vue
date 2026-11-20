<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Connect your email') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{
        __(
          'Send and receive email from the CRM, and keep every conversation on the right lead or deal.',
        )
      }}
    </p>

    <div
      v-if="connected"
      class="mt-8 flex items-center gap-3 rounded-6 border border-outline-gray-2 px-3 py-2.5"
    >
      <img
        v-if="connected.service?.logo"
        :src="connected.service.logo"
        alt=""
        class="size-6 shrink-0 object-contain"
      />
      <LucideMail v-else class="size-6 shrink-0 text-ink-gray-6" />
      <span class="flex min-w-0 flex-1 flex-col">
        <span class="truncate text-base text-ink-gray-9">
          {{ connected.email }}
        </span>
        <span class="truncate text-sm text-ink-gray-5">
          {{ connected.service?.label }}
        </span>
      </span>
      <Badge theme="green" :label="__('Connected')" />
    </div>

    <form
      v-else-if="selected"
      class="mt-8 flex flex-col gap-4"
      novalidate
      @submit.prevent="create"
    >
      <h2 class="text-lg-semibold text-ink-gray-9">{{ formTitle }}</h2>
      <p v-if="selected.help" class="text-p-sm text-ink-gray-6">
        {{ selected.help }}
        <a
          :href="selected.helpLink"
          target="_blank"
          rel="noopener"
          class="text-ink-gray-8 underline"
        >
          {{ __('Learn more') }}
        </a>
      </p>
      <FormControl
        v-model="form.email_id"
        type="email"
        :label="__('Email address')"
        placeholder="you@company.com"
        :description="
          googleSignIn
            ? __('The Gmail or Google Workspace email ID you\'re connecting.')
            : undefined
        "
        :error="errorOn('email_id')"
        required
        @blur="checkGmailAddress"
      />
      <SetupGmailAdminSteps
        v-if="googleSignIn && workspace"
        :client-id="oneClick.data?.GMail?.client_id"
      />
      <template v-if="selected.kind === 'frappe-mail'">
        <FormControl
          v-model="form.frappe_mail_site"
          :label="__('Frappe Mail site')"
          placeholder="https://frappemail.com"
          :error="errorOn('frappe_mail_site')"
          required
        />
        <FormControl
          v-model="form.api_key"
          :label="__('API key')"
          :error="errorOn('api_key')"
          required
        />
        <Password
          v-model="form.api_secret"
          :label="__('API secret')"
          :error="errorOn('api_secret')"
          required
        />
      </template>
      <Password
        v-else-if="!googleSignIn"
        v-model="form.password"
        :label="
          selected.kind === 'custom' ? __('Password') : __('App password')
        "
        :error="errorOn('password')"
        required
      >
        <template v-if="selected.service === 'GMail'" #description>
          {{
            __(
              'A 16-character password you create in your Google Account, not your Gmail password. Needs 2-Step Verification.',
            )
          }}
          <a
            href="https://support.google.com/accounts/answer/185833"
            target="_blank"
            rel="noopener"
            class="text-ink-gray-8 underline"
          >
            {{ __('How to create one') }}
          </a>
        </template>
      </Password>
      <template v-if="selected.kind === 'custom'">
        <FormControl
          v-model="form.email_server"
          :label="__('Incoming server (IMAP)')"
          placeholder="imap.example.com"
          :error="errorOn('email_server')"
          required
        />
        <FormControl
          v-model="form.smtp_server"
          :label="__('Outgoing server (SMTP)')"
          placeholder="smtp.example.com"
          :error="errorOn('smtp_server')"
          required
        />
      </template>
    </form>

    <div
      v-else
      role="radiogroup"
      :aria-label="__('Email provider')"
      class="mt-8 grid grid-cols-2 gap-2"
    >
      <button
        v-for="service in services"
        :key="service.service"
        type="button"
        role="radio"
        :aria-checked="choice === service"
        class="flex items-center gap-3 rounded-6 border px-3 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        :class="
          choice === service
            ? 'border-outline-gray-5 bg-surface-gray-2'
            : 'border-outline-gray-2 hover:border-outline-gray-3'
        "
        @click="choice = service"
        @dblclick="next"
      >
        <img
          v-if="service.logo"
          :src="service.logo"
          alt=""
          class="size-6 shrink-0 object-contain"
        />
        <LucideMail v-else class="size-6 shrink-0 text-ink-gray-6" />
        <span class="flex min-w-0 flex-col">
          <span class="truncate text-base text-ink-gray-9">
            {{ service.label }}
          </span>
          <span class="truncate text-sm text-ink-gray-5">
            {{ authLabel(service) }}
          </span>
        </span>
      </button>
    </div>

    <ErrorMessage v-if="error" class="mt-3" :message="error" />

    <div class="mt-auto pt-8">
      <div v-if="connected" class="flex justify-end">
        <Button variant="solid" :label="__('Continue')" @click="finish" />
      </div>
      <div v-else-if="!confirmSkip" class="flex items-center justify-end gap-2">
        <Button
          :label="__('Set up later')"
          :disabled="saving || connecting"
          @click="confirmSkip = true"
        />
        <Button
          v-if="googleSignIn && workspace"
          :label="__('Set up manually')"
          :disabled="connecting"
          @click="setUpManually"
        />
        <Button
          v-if="selected"
          variant="solid"
          :label="googleSignIn ? __('Continue') : __('Create')"
          :icon-right="
            googleSignIn && workspace ? 'lucide-arrow-up-right' : undefined
          "
          :loading="saving || connecting"
          @click="create"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Continue')"
          :disabled="!choice"
          :loading="connecting"
          @click="next"
        />
      </div>
      <div v-else>
        <Alert
          :title="__('Skip email for now?')"
          :description="
            __(
              'Emails won\'t show on leads and deals, you can\'t reply from the CRM, and incoming mail won\'t create leads. Connect it later from Settings.',
            )
          "
          :icon="false"
          :primary-action="{
            label: __('Connect email'),
            variant: 'solid',
            onClick: () => (confirmSkip = false),
          }"
          :secondary-action="{
            label: __('Skip anyway'),
            onClick: () => emit('skip'),
          }"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import SetupGmailAdminSteps from '@/components/Setup/SetupGmailAdminSteps.vue'
import { useCrmOnboarding } from '@/composables/onboarding'
import {
  Alert,
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  Password,
} from 'frappe-ui'
import {
  emptyForm,
  errorText,
  oauthMessage,
  services,
  validate,
} from '@framework/ui/components/EmailAccounts/services'
import {
  useEmailAccounts,
  useOneClick,
} from '@framework/ui/components/EmailAccounts/useEmailAccounts'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, inject, ref, shallowRef, watch } from 'vue'

const emit = defineEmits(['done', 'skip'])

const { capture } = useTelemetry()
const { completeStep } = useCrmOnboarding()

// loaded so the first mailbox becomes the default, and to pick up a one-click sign-in
const controller = useEmailAccounts('')
const oneClick = useOneClick()
controller.load()

const choice = shallowRef(null)
const selected = shallowRef(null)
const form = ref(emptyForm())
const invalid = ref(null)
const error = ref('')
const saving = ref(false)
const connecting = ref(false)
const confirmSkip = ref(false)
const connected = shallowRef(null)
// Gmail with one-click sign-in: a Workspace address signs in, a personal one needs an app password
const googleSignIn = ref(false)
const PERSONAL_GMAIL = /@(gmail|googlemail)\.com$/i
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// a Workspace address, whose admin must allow Frappe before it can sign in
const workspace = ref(false)

const preview = inject('setupPreview', null)
watch(
  () => [choice.value?.service, form.value.email_id],
  ([service, email]) => {
    if (!preview) return
    preview.provider = service
    preview.email = email.trim()
  },
)

const formTitle = computed(() =>
  selected.value.kind === 'custom'
    ? __('New custom email account')
    : __('New {0} account', [selected.value.label]),
)

function authLabel(service) {
  if (oneClick.data?.[service.service]) return __('Sign in')
  if (service.kind === 'frappe-mail') return __('API key')
  if (service.kind === 'custom') return __('IMAP and SMTP')
  if (service.outgoingOnly) return __('Sending only')
  return __('App password')
}

function errorOn(field) {
  return invalid.value?.field === field ? invalid.value.message : undefined
}

async function next() {
  const service = choice.value
  if (!service) return
  error.value = ''
  capture('setup_email_provider_selected', { provider: service.service })
  if (oneClick.loading) await oneClick.promise?.catch(() => {})
  googleSignIn.value = service.service === 'GMail' && !!oneClick.data?.GMail
  if (!googleSignIn.value && oneClick.data?.[service.service]) {
    if (await signIn(service.service)) return
  }
  selected.value = service
}

async function signIn(service, email) {
  connecting.value = true
  try {
    return await controller.connect(service, email)
  } catch (e) {
    error.value = errorText(e) || __('Could not start the sign-in')
    return true
  } finally {
    connecting.value = false
  }
}

// Setup's Back goes to the provider tiles first, before the previous step
const canGoBack = computed(() => Boolean(selected.value) && !saving.value)

function back() {
  if (!canGoBack.value) return false
  selected.value = null
  googleSignIn.value = false
  workspace.value = false
  form.value = emptyForm()
  invalid.value = null
  error.value = ''
  return true
}

defineExpose({ canGoBack, back })

async function create() {
  const service = selected.value
  if (googleSignIn.value) return continueWithGoogle()
  form.value.email_account_name = form.value.email_id.trim()
  invalid.value = validate(service, form.value)
  // the account name is the address, so its error belongs on the address
  if (invalid.value?.field === 'email_account_name')
    invalid.value = {
      field: 'email_id',
      message: __('Enter a valid email address'),
    }
  if (invalid.value) return
  saving.value = true
  error.value = ''
  try {
    await controller.create(service, form.value)
    const email = form.value.email_id.trim()
    await makeDefault(email)
    markConnected(service.service, email)
  } catch (e) {
    capture('setup_email_failed', { provider: service.service })
    error.value = errorText(e) || __('Could not connect: check your details')
  } finally {
    saving.value = false
  }
}

// checked when the field is left, as typing would flash the steps in and out
function checkGmailAddress() {
  const email = form.value.email_id.trim()
  if (!googleSignIn.value || !EMAIL.test(email)) return
  if (PERSONAL_GMAIL.test(email)) setUpManually()
  else workspace.value = true
}

function setUpManually() {
  googleSignIn.value = false
  workspace.value = false
}

async function continueWithGoogle() {
  const email = form.value.email_id.trim()
  invalid.value = EMAIL.test(email)
    ? null
    : { field: 'email_id', message: __('Enter a valid email address') }
  if (invalid.value) return
  if (PERSONAL_GMAIL.test(email)) return setUpManually()
  workspace.value = true
  error.value = ''
  if (!(await signIn('GMail', email))) setUpManually()
}

function markConnected(service, email) {
  connected.value = {
    email,
    service: services.find((s) => s.service === service),
  }
  completeStep('connect_your_email')
  capture('email_account_created', { provider: service })
}

// the mailbox connected in setup is the one the CRM sends and receives with
async function makeDefault(email) {
  const account = controller.accounts.find(
    (a) => a.email_id.toLowerCase() === email.toLowerCase(),
  )
  if (!account) return
  for (const kind of ['incoming', 'outgoing']) {
    if (account[`enable_${kind}`] && !account[`default_${kind}`])
      await controller.setDefault(kind, account.name)
  }
}

function finish() {
  emit('done', { provider: connected.value.service?.service })
}

const SIGN_IN_SERVICES = {
  google: 'GMail',
  microsoft: 'Outlook.com',
  yahoo: 'Yahoo Mail',
  yandex: 'Yandex.Mail',
}
const returned = controller.signIn
if (returned?.result === 'connected') {
  markConnected(SIGN_IN_SERVICES[returned.provider], returned.mailbox)
} else if (returned?.result) {
  error.value = oauthMessage(returned.result, returned.provider)
  // back on the Gmail form with the address and the admin steps
  if (returned.provider === 'google' && returned.mailbox) {
    selected.value = services.find((s) => s.service === 'GMail')
    form.value.email_id = returned.mailbox
    googleSignIn.value = true
    workspace.value = true
  }
}
watch(
  () => controller.signIn?.account,
  (account) =>
    account &&
    makeDefault(account.email_id).catch((e) => (error.value = errorText(e))),
)
</script>
