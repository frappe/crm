<template>
  <div class="mx-auto w-full max-w-sm px-4 py-8 text-center">
    <!-- Loading state while requesting OTP -->
    <div v-if="requestingOtp" class="py-8 text-center">
      <div class="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-200 dark:border-gray-700"
        :style="{ borderTopColor: 'var(--brand-primary)' }"></div>
      <p class="text-sm text-gray-500 dark:text-gray-400">Sending verification code…</p>
    </div>

    <!-- Fatal error (expired / tampered invitation) -->
    <div v-else-if="fatalError" class="py-8 text-center">
      <div
        class="mb-5 flex h-14 w-14 items-center justify-center rounded-full mx-auto bg-red-50 dark:bg-red-900/20"
      >
        <svg class="h-6 w-6 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">{{ fatalHeading }}</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">{{ fatalError }}</p>
      <p class="mt-4 text-xs text-gray-400 dark:text-gray-500">
        {{ fatalHint }}
      </p>
    </div>

    <!-- OTP entry form -->
    <template v-else>
      <div
        class="mb-5 flex h-14 w-14 items-center justify-center rounded-full mx-auto"
        style="background-color: color-mix(in srgb, var(--brand-primary) 15%, transparent)"
      >
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ color: 'var(--brand-primary)' }">
          <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
          <path d="M12 6v6l4 2"/>
        </svg>
      </div>

      <h2 class="mb-2 text-xl font-bold text-gray-900 dark:text-white">Verify your identity</h2>
      <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
        Enter the 6-digit code sent to your registered email address.
      </p>

      <!-- OTP inputs -->
      <div class="mb-4 flex justify-center gap-2">
        <input
          v-for="(_, i) in 6"
          :key="i"
          :ref="el => { if (el) inputRefs[i] = el }"
          v-model="digits[i]"
          type="text"
          inputmode="numeric"
          maxlength="1"
          :class="[
            'h-12 w-10 rounded-lg border-2 bg-white text-center text-lg font-bold text-gray-900 transition focus:outline-none dark:bg-gray-800 dark:text-white',
            errorMsg
              ? 'border-red-400 dark:border-red-600'
              : 'border-gray-200 focus:border-[color:var(--brand-primary)] dark:border-gray-700',
          ]"
          @input="onInput(i, $event)"
          @keydown="onKeydown(i, $event)"
          @paste.prevent="onPaste($event)"
        />
      </div>

      <!-- Countdown -->
      <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">
        <span v-if="countdown > 0">Code expires in {{ formatCountdown(countdown) }}</span>
        <span v-else class="text-red-500">Code expired.</span>
      </p>

      <!-- Error message -->
      <p v-if="errorMsg" class="mb-4 text-sm text-red-500 dark:text-red-400">
        {{ errorMsg }}
      </p>

      <!-- Verify button -->
      <button
        :disabled="loading || otpValue.length < 6"
        class="mb-4 w-full rounded-xl px-6 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 focus:outline-none disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="handleVerify"
      >
        <span v-if="loading">Verifying…</span>
        <span v-else>Verify Code</span>
      </button>

      <!-- Resend link -->
      <div class="flex items-center justify-center text-xs text-gray-400 dark:text-gray-500">
        <button
          :disabled="loading || resendLoading || countdown > 540"
          class="underline hover:text-gray-600 disabled:opacity-40 dark:hover:text-gray-300"
          @click="handleResend"
        >
          <span v-if="resendLoading">Sending…</span>
          <span v-else>Resend code</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  contract: { type: String, required: true },
  role: { type: String, required: true },
  token: { type: String, required: true },
})

const emit = defineEmits(['verified'])

// State
const digits = ref(['', '', '', '', '', ''])
const inputRefs = ref([])
const loading = ref(false)
const resendLoading = ref(false)
const errorMsg = ref('')
const requestingOtp = ref(true)
const fatalError = ref('')
const fatalHeading = ref('Link Invalid or Expired')
const fatalHint = ref('Please request a new signing link from the contract issuer.')

// 10-minute countdown
const countdown = ref(600)
let timer = null

const otpValue = computed(() => digits.value.join(''))

// ---------------------------------------------------------------------------
// Resources
// ---------------------------------------------------------------------------

const requestOtpResource = createResource({ url: 'crm.api.contracts.request_otp' })
const verifyOtpResource = createResource({ url: 'crm.api.contracts.verify_otp' })

// ---------------------------------------------------------------------------
// Lifecycle
// ---------------------------------------------------------------------------

onMounted(async () => {
  await doRequestOtp()
})

onUnmounted(() => {
  clearInterval(timer)
})

// ---------------------------------------------------------------------------
// OTP request
// ---------------------------------------------------------------------------

async function doRequestOtp() {
  requestingOtp.value = true
  fatalError.value = ''
  try {
    await requestOtpResource.fetch({
      contract: props.contract,
      role: props.role,
      token: props.token,
    })
    startCountdown()
    // Focus first digit input after render settles
    setTimeout(() => inputRefs.value[0]?.focus(), 100)
  } catch (err) {
    if (err?.exc_type === 'AuthenticationError') {
      fatalHeading.value = 'Link Invalid or Expired'
      fatalHint.value = 'Please request a new signing link from the contract issuer.'
      fatalError.value = 'This signing link has expired or is invalid.'
    } else {
      // Network / CSRF / server error — NOT an expired link.
      fatalHeading.value = 'Something went wrong'
      fatalHint.value = 'Please refresh the page and try again, or contact the contract issuer.'
      fatalError.value = err?.message || 'Failed to send verification code. Please try again.'
    }
  } finally {
    requestingOtp.value = false
  }
}

// ---------------------------------------------------------------------------
// Countdown
// ---------------------------------------------------------------------------

function startCountdown() {
  clearInterval(timer)
  countdown.value = 600
  timer = setInterval(() => {
    countdown.value = Math.max(0, countdown.value - 1)
  }, 1000)
}

function formatCountdown(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

// ---------------------------------------------------------------------------
// Input handlers
// ---------------------------------------------------------------------------

function onInput(i, event) {
  const val = event.target.value.replace(/\D/g, '')
  digits.value[i] = val.slice(-1)
  errorMsg.value = ''
  if (digits.value[i] && i < 5) {
    inputRefs.value[i + 1]?.focus()
  }
}

function onKeydown(i, event) {
  if (event.key === 'Backspace' && !digits.value[i] && i > 0) {
    inputRefs.value[i - 1]?.focus()
  }
  if (event.key === 'Enter' && otpValue.value.length === 6) {
    handleVerify()
  }
}

function onPaste(event) {
  const text = (event.clipboardData || window.clipboardData).getData('text')
  const cleaned = text.replace(/\D/g, '').slice(0, 6)
  for (let i = 0; i < 6; i++) {
    digits.value[i] = cleaned[i] || ''
  }
  if (cleaned.length === 6) {
    inputRefs.value[5]?.focus()
  }
}

// ---------------------------------------------------------------------------
// Verify
// ---------------------------------------------------------------------------

async function handleVerify() {
  if (otpValue.value.length < 6) return
  errorMsg.value = ''
  loading.value = true
  try {
    const data = await verifyOtpResource.fetch({
      contract: props.contract,
      role: props.role,
      token: props.token,
      otp: otpValue.value,
    })
    clearInterval(timer)
    emit('verified', {
      signingToken: data.signing_token,
      signatoryName: data.signatory_name,
    })
  } catch {
    errorMsg.value = 'Incorrect code. Please try again.'
    digits.value = ['', '', '', '', '', '']
    setTimeout(() => inputRefs.value[0]?.focus(), 50)
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// Resend
// ---------------------------------------------------------------------------

async function handleResend() {
  resendLoading.value = true
  errorMsg.value = ''
  try {
    await requestOtpResource.fetch({
      contract: props.contract,
      role: props.role,
      token: props.token,
    })
    startCountdown()
    digits.value = ['', '', '', '', '', '']
    setTimeout(() => inputRefs.value[0]?.focus(), 50)
  } catch {
    errorMsg.value = 'Failed to resend code. Please try again.'
  } finally {
    resendLoading.value = false
  }
}
</script>
