<template>
  <div class="mx-auto w-full max-w-lg px-4 py-8">
    <h2 class="mb-1 text-xl font-bold text-gray-900 dark:text-white">Ready to Commit?</h2>
    <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
      Review your commitment summary before submitting.
    </p>

    <!-- Summary card -->
    <div class="mb-6 rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
      <div class="mb-4 flex items-center gap-3">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full text-white"
          style="background-color: var(--brand-primary)"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <div>
          <p class="font-semibold text-gray-900 dark:text-white">
            {{ facilityCount }} {{ facilityCount === 1 ? 'facility' : 'facilities' }}
          </p>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ facilityList }}
          </p>
        </div>
      </div>

      <div class="rounded-lg bg-gray-50 px-4 py-3 dark:bg-gray-900">
        <div class="flex items-baseline justify-between">
          <span class="text-sm text-gray-500 dark:text-gray-400">Monthly commitment (incl. VAT)</span>
          <span class="text-xl font-black" :style="{ color: 'var(--brand-primary)' }">
            {{ fmtKes(grandTotalMonthly) }}
          </span>
        </div>
        <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">Rates are locked as agreed at sign-up.</p>
      </div>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
      {{ errorMsg }}
    </div>

    <!-- Actions -->
    <div class="flex flex-col gap-3">
      <button
        :disabled="loading"
        class="w-full rounded-xl px-6 py-3.5 text-sm font-semibold text-white shadow-md transition-opacity hover:opacity-90 focus:outline-none disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="handleCommit(true)"
      >
        <span v-if="loading && commitMode === 'commit'">Submitting...</span>
        <span v-else>Commit &amp; Opt In</span>
      </button>

      <button
        :disabled="loading"
        class="w-full rounded-xl border border-gray-200 bg-white px-6 py-3.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 focus:outline-none disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="handleCommit(false)"
      >
        <span v-if="loading && commitMode === 'later'">Saving...</span>
        <span v-else>I'll Decide Later</span>
      </button>
    </div>

    <div class="mt-4 flex justify-start">
      <button
        :disabled="loading"
        class="text-sm underline text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
        @click="handleBack"
      >
        Back
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { useOptInStore } from './useOptInStore.js'

const props = defineProps({
  networkSlug: { type: String, required: true },
})

const emit = defineEmits(['submitted', 'back'])

const store = useOptInStore()

const loading = ref(false)
const commitMode = ref('') // 'commit' | 'later'
const errorMsg = ref('')

const facilityCount = computed(() => (store.selectedFacilities || []).length)
const facilityList = computed(() =>
  (store.selectedFacilities || [])
    .map(f => f.facility_name)
    .join(', ')
)
const grandTotalMonthly = computed(() => store.pricing?.grand_total_monthly || 0)

function fmtKes(v) {
  const n = parseFloat(v || 0)
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

const submitResource = createResource({ url: 'crm.api.optin.submit_async' })

async function handleCommit(committed) {
  loading.value = true
  commitMode.value = committed ? 'commit' : 'later'
  errorMsg.value = ''

  const payload = {
    contact: store.contact,
    witness: store.witness,
    facilities: store.selectedFacilities,
    pricing: store.pricing?.facilities || [],
    tc_doc_name: store.termsDocName,
    tc_doc_hash: store.termsDocHash,
    committed,
  }

  try {
    const data = await submitResource.fetch({
      signing_token: store.signingToken,
      email: store.contact.email,
      network_slug: props.networkSlug,
      expiry: store.signingExpiry,
      payload_json: JSON.stringify(payload),
    })
    store.setSubmissionRef(data.submission_ref)
    emit('submitted', data.submission_ref)
  } catch (err) {
    errorMsg.value = (err && err.message) ? err.message : 'Submission failed. Please try again.'
  } finally {
    loading.value = false
    commitMode.value = ''
  }
}

function handleBack() {
  // Reset only acceptance — keep termsHtml so T&C doesn't need to reload
  store.setTermsAccepted(false)
  emit('back')
}
</script>
