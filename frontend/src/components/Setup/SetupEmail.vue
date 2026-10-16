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

    <RadioGroup
      v-if="!editing"
      v-model="state.service"
      class="mt-6"
      padded
      :label="__('Email provider')"
    >
      <Radio
        v-for="service in services"
        :key="service.name"
        :value="service.name"
        :description="HINTS[service.name]"
      >
        <template #label>
          <span class="flex items-center gap-2">
            <img :src="service.icon" class="size-4" alt="" />
            {{ service.name }}
          </span>
        </template>
      </Radio>
    </RadioGroup>

    <div v-else class="mt-6 flex flex-col gap-4">
      <div class="flex items-center gap-2 border-b border-outline-gray-1 pb-3">
        <img :src="selected.icon" class="size-4" alt="" />
        <span class="text-base font-medium text-ink-gray-9">
          {{ selected.name }}
        </span>
        <Button
          class="ml-auto"
          variant="ghost"
          :label="__('Change')"
          :disabled="account.loading"
          @click="editing = false"
        />
      </div>
      <TextInput
        v-model="state.email_id"
        type="email"
        :label="__('Email address')"
        placeholder="you@company.com"
      />
      <template v-if="selected.custom">
        <TextInput
          v-model="state.frappe_mail_site"
          :label="__('Frappe Mail site')"
          placeholder="https://frappemail.com"
        />
        <TextInput v-model="state.api_key" :label="__('API key')" />
        <Password v-model="state.api_secret" :label="__('API secret')" />
      </template>
      <Password v-else v-model="state.password" :label="__('App password')">
        <template #description>
          {{ selected.info }}
          <a
            :href="selected.link"
            target="_blank"
            class="text-ink-gray-7 underline underline-offset-2"
          >
            {{ __('here') }}
          </a>
        </template>
      </Password>
      <div>
        <Button
          variant="ghost"
          class="-ml-2"
          :label="__('Sync options')"
          :aria-expanded="showSyncOptions"
          @click="showSyncOptions = !showSyncOptions"
        >
          <template #suffix>
            <LucideChevronRight
              class="size-4 transition-transform duration-150 motion-reduce:transition-none"
              :class="{ 'rotate-90': showSyncOptions }"
            />
          </template>
        </Button>
        <div
          v-show="showSyncOptions"
          class="mt-1 divide-y divide-outline-gray-1"
        >
          <Switch
            v-model="state.enable_incoming"
            class="py-2.5"
            :label="__('Receive email')"
            :description="__('Pull replies into lead and deal timelines')"
          />
          <Switch
            v-model="state.enable_outgoing"
            class="py-2.5"
            :label="__('Send email')"
            :description="__('Reply and send from the CRM')"
          />
        </div>
      </div>
      <ErrorMessage :message="error" />
    </div>

    <div class="relative mt-auto pt-8">
      <div
        class="flex items-center justify-between"
        :class="{ invisible: confirmSkip }"
      >
        <Button
          variant="ghost"
          :label="__('Set up later')"
          :disabled="account.loading"
          @click="confirmSkip = true"
        />
        <Button
          v-if="editing"
          variant="solid"
          :label="__('Connect account')"
          :loading="account.loading"
          @click="connect"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Continue')"
          :disabled="!state.service"
          @click="editing = true"
        />
      </div>
      <div
        v-if="confirmSkip"
        class="absolute inset-x-0 bottom-0 bg-surface-base pt-4"
      >
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
import LucideChevronRight from '~icons/lucide/chevron-right'
import { services, validateInputs } from '@/components/Settings/emailConfig'
import { useCrmOnboarding } from '@/composables/onboarding'
import {
  Alert,
  Button,
  ErrorMessage,
  Password,
  Radio,
  RadioGroup,
  Switch,
  TextInput,
  createResource,
  toast,
} from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, inject, reactive, ref, watch } from 'vue'

const emit = defineEmits(['done', 'skip'])

const { capture } = useTelemetry()
const { completeStep } = useCrmOnboarding()

const HINTS = {
  GMail: __('Google Workspace or Gmail'),
  Outlook: __('Microsoft 365 or Outlook.com'),
  Sendgrid: __('SMTP with an API key'),
  SparkPost: __('SMTP with an API key'),
  Yahoo: __('IMAP with an app password'),
  Yandex: __('IMAP with an app password'),
  'Frappe Mail': __('Site, API key and secret'),
}

const state = reactive({
  service: undefined,
  email_id: '',
  password: '',
  frappe_mail_site: '',
  api_key: '',
  api_secret: '',
  enable_incoming: true,
  enable_outgoing: true,
})
const editing = ref(false)
const showSyncOptions = ref(false)
const confirmSkip = ref(false)
const error = ref('')

const preview = inject('setupPreview', null)
watch(
  () => state.service,
  (service) => preview && (preview.provider = service),
)

const selected = computed(() =>
  services.find((service) => service.name === state.service),
)

const account = createResource({
  url: 'crm.api.settings.create_email_account',
  onSuccess() {
    toast.success(__('Email account connected'))
    completeStep('connect_your_email')
    capture('email_account_created')
    emit('done', { provider: state.service })
  },
  onError(err) {
    error.value =
      err.messages?.[0] || __('Could not connect: check your credentials')
  },
})

function connect() {
  const data = {
    ...state,
    email_account_name: state.email_id,
    default_incoming: state.enable_incoming,
    default_outgoing: state.enable_outgoing,
  }
  error.value = validateInputs(data, selected.value.custom)
  if (error.value) return
  account.submit({ data })
}
</script>
