<template>
  <div class="mx-auto w-full max-w-lg px-4 py-8">
    <!-- Loud block state: the email is not a pre-qualified contact for this
         network, or the sender is rate-limited. Shown instead of the form. -->
    <div v-if="blockState" class="flex flex-col items-center py-8 text-center">
      <div
        :class="[
          'mb-5 flex h-16 w-16 items-center justify-center rounded-full',
          blockState === 'rate_limited'
            ? 'bg-amber-100 dark:bg-amber-900/30'
            : 'bg-red-100 dark:bg-red-900/30',
        ]"
      >
        <svg
          v-if="blockState === 'rate_limited'"
          class="h-8 w-8 text-amber-600 dark:text-amber-400"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
        </svg>
        <svg
          v-else
          class="h-8 w-8 text-red-600 dark:text-red-400"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        >
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="m15 9-6 6" /><path d="m9 9 6 6" />
        </svg>
      </div>

      <h2 class="mb-2 text-xl font-bold text-gray-900 dark:text-white">
        {{ blockState === 'rate_limited' ? 'Too many attempts' : "This email isn't registered" }}
      </h2>

      <p class="mb-2 max-w-sm text-sm text-gray-600 dark:text-gray-300">
        <template v-if="blockState === 'rate_limited'">
          For your security we've paused new codes for a few minutes. Please wait, then try again.
        </template>
        <template v-else>
          We couldn't find
          <span class="font-semibold text-gray-900 dark:text-white">{{ form.email }}</span>
          on the pre-qualified contact list for
          <span class="font-semibold text-gray-900 dark:text-white">{{ networkName }}</span>.
        </template>
      </p>

      <p v-if="blockState !== 'rate_limited'" class="mb-6 max-w-sm text-xs text-gray-400 dark:text-gray-500">
        Only the contact your facility registered with can opt in. Check the spelling, or use that
        email address.
        <template v-if="contactEmail">
          Still stuck? Email
          <a :href="'mailto:' + contactEmail" class="underline hover:text-gray-600 dark:hover:text-gray-300">{{ contactEmail }}</a>.
        </template>
      </p>

      <div class="flex w-full max-w-xs flex-col gap-2">
        <button
          type="button"
          class="w-full rounded-xl px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 focus:outline-none"
          style="background-color: var(--brand-primary)"
          @click="handleTryAgain"
        >
          {{ blockState === 'rate_limited' ? 'Try Again' : 'Try a Different Email' }}
        </button>
        <button
          type="button"
          class="w-full rounded-xl border border-gray-200 bg-white px-6 py-3 text-sm font-medium text-gray-600 transition hover:bg-gray-50 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="emit('back')"
        >
          Back to Home
        </button>
      </div>
    </div>

    <template v-else>
    <h2 class="mb-1 text-xl font-bold text-gray-900 dark:text-white">Your Details</h2>
    <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
      Enter the details for the registered contact at your facility.
    </p>

    <form class="space-y-4" @submit.prevent="handleContinue">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">First Name</label>
          <input v-model="form.first_name" type="text" placeholder="Jane"
            class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">Last Name</label>
          <input v-model="form.last_name" type="text" placeholder="Doe"
            class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">
          Email Address <span class="text-red-500">*</span>
        </label>
        <input v-model="form.email" type="email" placeholder="jane.doe@hospital.or.ke" required
          :class="['w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500',
            emailError ? 'border-red-400 dark:border-red-600' : 'border-gray-200 dark:border-gray-700']"
        />
        <p v-if="emailError" class="mt-1 text-xs text-red-500">{{ emailError }}</p>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">Mobile Number</label>
        <input v-model="form.mobile_no" type="tel" placeholder="0712 345 678"
          :class="['w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500',
            mobileError ? 'border-red-400 dark:border-red-600' : 'border-gray-200 dark:border-gray-700']"
        />
        <p v-if="mobileError" class="mt-1 text-xs text-red-500">{{ mobileError }}</p>
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">Organisation / Facility Name</label>
        <input v-model="form.organisation" type="text" placeholder="Kenyatta National Hospital"
          class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
        />
      </div>

      <div>
        <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">Your Role / Title</label>
        <input v-model="form.role" type="text" placeholder="Chief Executive Officer"
          class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
        />
      </div>

      <!-- OTP delivery channel -->
      <div>
        <label class="mb-1 block text-xs font-medium text-gray-700 dark:text-gray-300">
          Send my verification code by
        </label>
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            :aria-pressed="channel === 'email'"
            :class="channelBtnClass(channel === 'email')"
            :style="channel === 'email' ? { backgroundColor: 'var(--brand-primary)', borderColor: 'var(--brand-primary)' } : {}"
            @click="channel = 'email'"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/>
            </svg>
            Email
          </button>
          <button
            type="button"
            :aria-pressed="channel === 'sms'"
            :class="channelBtnClass(channel === 'sms')"
            :style="channel === 'sms' ? { backgroundColor: 'var(--brand-primary)', borderColor: 'var(--brand-primary)' } : {}"
            @click="channel = 'sms'"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            SMS
          </button>
        </div>
        <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
          The code is sent to the registered contact on file for your facility.
        </p>
      </div>

      <div v-if="generalError" class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
        {{ generalError }}
      </div>

      <div class="flex flex-col gap-2 pt-2">
        <button
          type="submit"
          :disabled="loading || !form.email"
          class="w-full rounded-xl px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 focus:outline-none disabled:opacity-50"
          style="background-color: var(--brand-primary)"
        >
          <span v-if="loading">Sending code...</span>
          <span v-else>Continue</span>
        </button>

        <button
          type="button"
          :disabled="loading"
          class="w-full rounded-xl border border-gray-200 bg-white px-6 py-3 text-sm font-medium text-gray-600 transition hover:bg-gray-50 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="emit('back')"
        >
          Back
        </button>

        <button
          v-if="hasSigningToken"
          type="button"
          :disabled="loading"
          class="w-full rounded-xl border border-gray-200 bg-white px-6 py-3 text-sm font-medium text-gray-600 transition hover:bg-gray-50 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          @click="handleSavePartial"
        >
          Save &amp; Come Back Later
        </button>
      </div>
    </form>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { useOptInStore } from './useOptInStore.js'

const props = defineProps({
  networkSlug: { type: String, required: true },
})

const emit = defineEmits(['otp-requested', 'partial-saved', 'back'])

const store = useOptInStore()

const form = reactive({
  first_name: store.contact.first_name || '',
  last_name: store.contact.last_name || '',
  email: store.contact.email || '',
  mobile_no: store.contact.mobile_no || '',
  organisation: store.contact.organisation || '',
  role: store.contact.role || '',
})

const loading = ref(false)
const emailError = ref('')
const mobileError = ref('')
const generalError = ref('')
// '' = form shown; 'not_registered' | 'rate_limited' = loud block state shown
const blockState = ref('')

const hasSigningToken = computed(() => !!store.signingToken)
const networkName = computed(() => store.networkConfig?.display_name || 'this network')
const contactEmail = computed(() => store.networkConfig?.contact_email || '')

// OTP delivery channel — persisted in the store so the OTP gate can honour it on resend
const channel = computed({
  get: () => store.otpChannel,
  set: (val) => store.setOtpChannel(val),
})

function channelBtnClass(active) {
  return [
    'flex items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-medium transition focus:outline-none',
    active
      ? 'text-white'
      : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700',
  ]
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function validateMobile(mobile) {
  if (!mobile) return true
  const digits = mobile.replace(/\D/g, '')
  return digits.length >= 10 && digits.length <= 13
}

function validate() {
  emailError.value = ''
  mobileError.value = ''
  let valid = true
  if (!validateEmail(form.email)) {
    emailError.value = 'Please enter a valid email address.'
    valid = false
  }
  if (form.mobile_no && !validateMobile(form.mobile_no)) {
    mobileError.value = 'Mobile number must be 10–13 digits.'
    valid = false
  }
  return valid
}

const verifyResource = createResource({ url: 'crm.api.optin.verify_prequalified' })

async function handleContinue() {
  if (!validate()) return
  generalError.value = ''
  blockState.value = ''
  loading.value = true
  store.setContact({ ...form })

  let data
  try {
    data = await verifyResource.fetch({
      email: form.email,
      network_slug: props.networkSlug,
      channel: store.otpChannel,
    })
  } catch {
    // Real network/server error — let them retry rather than mislabel them as
    // unregistered (no code was sent, so proceeding to the gate is pointless).
    generalError.value = 'Something went wrong sending your code. Please try again.'
    loading.value = false
    return
  }
  loading.value = false

  // matched  -> code dispatched, go to the OTP gate.
  // otherwise -> loud block state (rate-limited vs. not a registered contact).
  if (data && data.matched) {
    emit('otp-requested')
    return
  }
  blockState.value = data && data.rate_limited ? 'rate_limited' : 'not_registered'
}

function handleTryAgain() {
  blockState.value = ''
}

const savePartialResource = createResource({ url: 'crm.api.optin.save_partial' })

async function handleSavePartial() {
  if (!validate()) return
  generalError.value = ''
  loading.value = true
  store.setContact({ ...form })
  try {
    const data = await savePartialResource.fetch({
      signing_token: store.signingToken,
      email: form.email,
      network_slug: props.networkSlug,
      expiry: store.signingExpiry,
      contact_json: JSON.stringify({ ...form }),
    })
    emit('partial-saved', data?.submission_ref || '')
  } catch (err) {
    generalError.value = (err && err.message) ? err.message : 'Could not save. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
