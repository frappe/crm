<template>
  <div class="mx-auto w-full max-w-sm px-4 py-8 text-center">
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
      Enter the 6-digit code sent to your
      <span class="font-medium text-gray-700 dark:text-gray-300">{{ channelNoun }}</span>.
    </p>

    <!-- OTP input -->
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
          errorMsg ? 'border-red-400 dark:border-red-600' : 'border-gray-200 focus:border-[color:var(--brand-primary)] dark:border-gray-700',
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

    <!-- Error -->
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
      <span v-if="loading">Verifying...</span>
      <span v-else>Verify Code</span>
    </button>

    <!-- Resend + back -->
    <div class="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
      <button
        :disabled="loading || resendLoading || countdown > 540"
        class="underline hover:text-gray-600 disabled:opacity-40 dark:hover:text-gray-300"
        @click="handleResend"
      >
        <span v-if="resendLoading">Sending...</span>
        <span v-else>Resend code</span>
      </button>

      <button
        class="underline hover:text-gray-600 dark:hover:text-gray-300"
        @click="emit('back')"
      >
        Change email
      </button>
    </div>

    <!-- Switch delivery channel -->
    <p class="mt-4 text-xs text-gray-400 dark:text-gray-500">
      <button
        :disabled="loading || resendLoading"
        class="underline hover:text-gray-600 disabled:opacity-40 dark:hover:text-gray-300"
        @click="switchChannel"
      >
        {{ switchLabel }}
      </button>
    </p>

    <!-- Network contact help -->
    <p
      v-if="networkContactEmail"
      class="mt-6 text-xs text-gray-400 dark:text-gray-500"
    >
      Need help? Contact
      <a :href="'mailto:' + networkContactEmail" class="underline hover:text-gray-600 dark:hover:text-gray-300">
        {{ networkContactEmail }}
      </a>
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { useOptInStore } from './useOptInStore.js'

const props = defineProps({
  email: { type: String, required: true },
  networkSlug: { type: String, required: true },
})

const emit = defineEmits(['verified', 'back'])

const store = useOptInStore()
const networkContactEmail = computed(() => store.networkConfig?.contact_email || '')

// Delivery-channel display + switch affordance
const channelNoun = computed(() =>
  store.otpChannel === 'sms' ? 'registered mobile number' : 'email',
)
const switchLabel = computed(() =>
  store.otpChannel === 'sms'
    ? 'Prefer email? Send the code by email instead'
    : "Didn't get the email? Send the code by SMS instead",
)

const digits = ref(['', '', '', '', '', ''])
const inputRefs = ref([])
const loading = ref(false)
const resendLoading = ref(false)
const errorMsg = ref('')

// 10-minute countdown (600 seconds)
const countdown = ref(600)
let timer = null

onMounted(() => {
  startCountdown()
  // Focus first input
  setTimeout(() => inputRefs.value[0]?.focus(), 100)
})

onUnmounted(() => {
  clearInterval(timer)
})

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

const otpValue = computed(() => digits.value.join(''))

function onInput(i, event) {
  const val = event.target.value.replace(/\D/g, '')
  digits.value[i] = val.slice(-1)
  errorMsg.value = ''
  // Auto-advance
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

const verifyOtpResource = createResource({ url: 'crm.api.optin.verify_otp' })

async function handleVerify() {
  if (otpValue.value.length < 6) return
  errorMsg.value = ''
  loading.value = true
  try {
    const data = await verifyOtpResource.fetch({
      email: props.email,
      network_slug: props.networkSlug,
      otp: otpValue.value,
    })
    clearInterval(timer)
    store.setSigningToken(data.signing_token, data.expiry)
    store.setFacilities(data.facilities || [])
    emit('verified', data.signing_token, data.facilities || [])
  } catch {
    // Same message for wrong OTP and unregistered email — no info leak
    errorMsg.value = 'Incorrect code. Please try again.'
    digits.value = ['', '', '', '', '', '']
    setTimeout(() => inputRefs.value[0]?.focus(), 50)
  } finally {
    loading.value = false
  }
}

const resendResource = createResource({ url: 'crm.api.optin.verify_prequalified' })

async function handleResend() {
  resendLoading.value = true
  errorMsg.value = ''
  try {
    await resendResource.fetch({
      email: props.email,
      network_slug: props.networkSlug,
      channel: store.otpChannel,
    })
  } catch {
    // Silent — same as initial call
  } finally {
    resendLoading.value = false
    startCountdown()
    digits.value = ['', '', '', '', '', '']
    setTimeout(() => inputRefs.value[0]?.focus(), 50)
  }
}

// Flip the delivery channel and immediately resend the code via the other channel.
function switchChannel() {
  store.setOtpChannel(store.otpChannel === 'sms' ? 'email' : 'sms')
  handleResend()
}
</script>
