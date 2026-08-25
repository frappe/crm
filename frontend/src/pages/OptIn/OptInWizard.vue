<template>
  <div
    class="min-h-screen bg-gray-50 dark:bg-gray-950"
    :style="brandStyle"
  >
    <!-- Wrapper card (steps 1-6): a bounded, viewport-fitting column — fixed header,
         scrollable body — so the wizard never grows past one screen. -->
    <div
      v-if="showCard"
      class="mx-auto flex h-screen max-w-2xl flex-col overflow-hidden bg-white shadow-xl dark:bg-gray-900 md:my-[4vh] md:h-[92vh] md:rounded-2xl"
    >
      <!-- Card header: logo + progress bar -->
      <div v-if="store.step > 0 && store.step < 7" class="shrink-0 border-b border-gray-100 px-4 py-5 dark:border-gray-800">
        <!-- Network logo + name, centered at the top of the wizard -->
        <div class="mb-4 flex flex-col items-center gap-2 text-center">
          <img
            v-if="networkConfig && networkConfig.logo_url"
            :src="networkConfig.logo_url"
            class="h-10 w-auto object-contain"
            :alt="networkConfig.display_name || ''"
          />
          <span class="text-base font-semibold text-gray-800 dark:text-gray-200">
            {{ networkConfig ? networkConfig.display_name : 'CareverseHIMS' }}
          </span>
        </div>
        <StepProgressBar :active-step="progressStep" />
      </div>

      <!-- Step content -->
      <div class="flex-1 overflow-y-auto">
        <!-- Step 1: Contact form -->
        <StepContact
          v-if="store.step === 1 && !store.showOtpGate"
          :network-slug="networkSlug"
          @otp-requested="store.setShowOtpGate(true)"
          @partial-saved="onPartialSaved"
          @back="store.setStep(0)"
        />

        <!-- OTP gate (between steps 1 and 2) -->
        <OtpGate
          v-if="store.showOtpGate"
          :email="store.contact.email"
          :network-slug="networkSlug"
          @verified="onOtpVerified"
          @back="store.setShowOtpGate(false)"
        />

        <!-- Step 2: Facilities -->
        <StepFacilities
          v-if="store.step === 2"
          :facilities="store.facilities"
          @continue="onFacilitiesSelected"
          @back="store.setStep(1)"
        />

        <!-- Step 3: Pricing -->
        <StepPricing
          v-if="store.step === 3"
          :network-slug="networkSlug"
          @continue="store.setStep(4)"
          @back="onBackFromPricing"
        />

        <!-- Step 4: Review -->
        <StepReview
          v-if="store.step === 4"
          @continue="store.setStep(5)"
          @back="store.setStep(3)"
          @edit-contact="onEditContact"
          @edit-facilities="onEditFacilities"
        />

        <!-- Step 5: Terms -->
        <StepTerms
          v-if="store.step === 5"
          :network-slug="networkSlug"
          :is-active="store.step === 5"
          @continue="store.setStep(6)"
          @back="onBackFromTerms"
        />

        <!-- Step 6: Commit -->
        <StepCommit
          v-if="store.step === 6"
          :network-slug="networkSlug"
          @submitted="onSubmitted"
          @back="onBackFromCommit"
        />
      </div>
    </div>

    <!-- Step 0: Landing (full page) -->
    <StepLanding
      v-if="store.step === 0"
      :network-config="networkConfig"
      @next="store.setStep(1)"
    />

    <!-- Step 7: Progress (full page, centred) -->
    <div v-if="store.step === 7" class="flex min-h-screen items-center justify-center px-4">
      <div class="w-full max-w-sm bg-white rounded-xl shadow-lg py-6 dark:bg-gray-900">
        <StepProgress
          :network-slug="networkSlug"
          @complete="store.setStep(8)"
          @retry="store.setStep(6)"
        />
      </div>
    </div>

    <!-- Step 8: Success (full page, centred) -->
    <div v-if="store.step === 8" class="flex min-h-screen items-center justify-center px-4">
      <div class="w-full max-w-sm bg-white rounded-xl shadow-lg py-6 dark:bg-gray-900">
        <StepSuccess />
      </div>
    </div>

    <!-- Partial saved interstitial -->
    <div v-if="showPartialSaved" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div class="w-full max-w-sm rounded-xl bg-white p-6 text-center shadow-xl dark:bg-gray-800">
        <div
          class="mb-4 flex h-12 w-12 items-center justify-center rounded-full mx-auto"
          style="background-color: var(--brand-primary)"
        >
          <svg class="h-6 w-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <h3 class="mb-2 font-bold text-gray-900 dark:text-white">Progress saved!</h3>
        <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">
          We've sent a resume link to your email address. You can close this page and continue later.
        </p>
        <p v-if="partialRef" class="mb-4 font-mono text-xs text-gray-400 dark:text-gray-500">
          Reference: {{ partialRef }}
        </p>
        <button
          class="w-full rounded-xl px-5 py-2.5 text-sm font-semibold text-white"
          style="background-color: var(--brand-primary)"
          @click="showPartialSaved = false"
        >
          OK
        </button>
      </div>
    </div>

    <!-- Settings loading error -->
    <div v-if="settingsError" class="fixed bottom-4 right-4 z-50 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700 shadow-lg dark:bg-amber-900/20 dark:text-amber-400">
      Could not load network configuration. Default branding applied.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { useOptInStore } from './useOptInStore.js'
import StepProgressBar from './StepProgressBar.vue'
import StepLanding from './StepLanding.vue'
import StepContact from './StepContact.vue'
import OtpGate from './OtpGate.vue'
import StepFacilities from './StepFacilities.vue'
import StepPricing from './StepPricing.vue'
import StepReview from './StepReview.vue'
import StepTerms from './StepTerms.vue'
import StepCommit from './StepCommit.vue'
import StepProgress from './StepProgress.vue'
import StepSuccess from './StepSuccess.vue'

const props = defineProps({
  networkSlug: { type: String, default: '' },
})

const store = useOptInStore()
store.networkSlug = props.networkSlug

const settingsError = ref(false)
const showPartialSaved = ref(false)
const partialRef = ref('')

const networkConfig = computed(() => store.networkConfig)

const DEFAULT_BRAND = '#C0101A'

// Derive brand style from network config
const brandStyle = computed(() => {
  const color = (networkConfig.value && networkConfig.value.primary_colour) || DEFAULT_BRAND
  return { '--brand-primary': color }
})

// Show card wrapper for steps 1–6
const showCard = computed(() =>
  (store.step >= 1 && store.step <= 6) || store.showOtpGate
)

// Map wizard step to progress bar step (1-6)
const progressStep = computed(() => {
  if (store.showOtpGate) return 2
  const map = { 1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 6 }
  return map[store.step] || 1
})

const settingsResource = createResource({ url: 'crm.api.optin.get_settings' })

onMounted(async () => {
  try {
    const data = await settingsResource.fetch({ network_slug: props.networkSlug })
    store.setNetworkConfig(data.network_config || null)
  } catch {
    settingsError.value = true
    store.setNetworkConfig({
      display_name: 'CareverseHIMS',
      logo_url: '',
      primary_colour: '#C0101A',
      contact_email: '',
      footer_legal_name: 'Tiberbu Healthnet Solutions',
    })
  }
})

function onOtpVerified() {
  store.setShowOtpGate(false)
  store.setStep(2)
}

function onFacilitiesSelected() {
  store.setPricing(null)
  store.setStep(3)
}

function onBackFromPricing() {
  store.setStep(2)
}

function onEditContact() {
  store.setStep(1)
}

function onEditFacilities() {
  store.setPricing(null)
  store.setStep(2)
}

function onBackFromTerms() {
  // Reset terms state when leaving step 5 going backwards
  store.setTermsAccepted(false)
  store.setStep(4)
}

function onBackFromCommit() {
  // Reset acceptance on back from commit (spec: T&C checkbox resets on any back nav)
  store.setTermsAccepted(false)
  store.setStep(5)
}

function onSubmitted(submissionRef) {
  store.setSubmissionRef(submissionRef)
  store.setStep(7)
}

function onPartialSaved(ref) {
  partialRef.value = ref
  showPartialSaved.value = true
}
</script>
