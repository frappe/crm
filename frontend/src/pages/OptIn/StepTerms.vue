<template>
  <div class="mx-auto w-full max-w-2xl px-4 py-6">
    <div class="mb-1 flex items-center gap-2.5">
      <span
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
        style="background-color: color-mix(in srgb, var(--brand-primary) 12%, transparent)"
      >
        <svg
          class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          :style="{ color: 'var(--brand-primary)' }"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="M9 13h6M9 17h4" />
        </svg>
      </span>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">Terms &amp; Conditions</h2>
    </div>
    <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">
      Please read the full Terms &amp; Conditions carefully before accepting.
    </p>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-transparent" :style="{ borderTopColor: 'var(--brand-primary)' }" />
    </div>

    <!-- Error -->
    <div v-else-if="errorMsg" class="rounded-xl bg-red-50 px-6 py-8 text-center dark:bg-red-900/10">
      <p class="text-sm text-red-600 dark:text-red-400">{{ errorMsg }}</p>
      <button class="mt-3 text-xs underline text-red-600 hover:text-red-800 dark:text-red-400" @click="loadTerms">Retry</button>
    </div>

    <template v-else-if="termsLoaded">
      <!-- Scrollable T&C panel -->
      <div
        ref="scrollPanel"
        class="tc-panel mb-4 max-h-[52vh] overflow-y-auto rounded-2xl border border-gray-200 bg-white p-6 text-sm leading-relaxed text-gray-700 shadow-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
        @scroll="onScroll"
        v-html="store.termsHtml"
      />

      <!-- Scroll hint -->
      <p v-if="!scrolledToBottom" class="mb-3 text-xs text-amber-600 dark:text-amber-400">
        Please scroll to the bottom to enable acceptance.
      </p>

      <!-- Acceptance checkbox -->
      <label class="flex cursor-pointer items-start gap-3">
        <input
          v-model="accepted"
          type="checkbox"
          :disabled="!scrolledToBottom"
          class="mt-0.5 h-4 w-4 cursor-pointer rounded border-gray-300 accent-[color:var(--brand-primary)] disabled:cursor-not-allowed disabled:opacity-50"
        />
        <span
          :class="[
            'text-sm',
            scrolledToBottom ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 dark:text-gray-600',
          ]"
        >
          I have read and accept the Terms &amp; Conditions
        </span>
      </label>
    </template>

    <!-- Footer nav -->
    <div class="mt-6 flex items-center justify-between">
      <button
        class="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="handleBack"
      >
        Back
      </button>
      <button
        :disabled="!accepted"
        class="rounded-xl px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="handleContinue"
      >
        Continue
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { useOptInStore } from './useOptInStore.js'

const props = defineProps({
  networkSlug: { type: String, required: true },
  // isActive is toggled by parent when navigating back to this step
  isActive: { type: Boolean, default: true },
})

const emit = defineEmits(['continue', 'back'])

const store = useOptInStore()

const loading = ref(false)
const errorMsg = ref('')
const termsLoaded = ref(false)
const scrolledToBottom = ref(false)
const accepted = ref(false)
const scrollPanel = ref(null)

// Reset is handled by onMounted — v-if in parent destroys and recreates this
// component on every visit, so onMounted fires fresh each time. If this ever
// moves to v-show or keep-alive, add an explicit watch here.

const termsResource = createResource({ url: 'crm.api.optin.get_terms_text' })

async function loadTerms() {
  if (store.termsHtml) {
    termsLoaded.value = true
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const mflCodes = (store.selectedFacilities || []).map(f => f.mfl_code)
    const data = await termsResource.fetch({
      signing_token: store.signingToken,
      email: store.contact.email,
      network_slug: props.networkSlug,
      expiry: store.signingExpiry,
      selected_mfl_codes: JSON.stringify(mflCodes),
    })
    store.setTerms(data.html, data.doc_name, data.doc_hash)
    termsLoaded.value = true
  } catch (err) {
    errorMsg.value = (err && err.message) ? err.message : 'Failed to load Terms & Conditions. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTerms()
  // Reset state on mount (handles fresh navigation to this step)
  accepted.value = false
  scrolledToBottom.value = false
  store.setTermsAccepted(false)
})

function onScroll() {
  if (!scrollPanel.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollPanel.value
  // Allow 10px tolerance
  if (scrollTop + clientHeight >= scrollHeight - 10) {
    scrolledToBottom.value = true
  }
}

function handleBack() {
  accepted.value = false
  scrolledToBottom.value = false
  store.setTermsAccepted(false)
  emit('back')
}

function handleContinue() {
  store.setTermsAccepted(true)
  emit('continue', store.termsDocName, store.termsDocHash)
}
</script>

<style scoped>
/* T&C typography — UI style layer. Colour-neutral on purpose: the panel supplies the
   text colour (light + dark), so these rules only set spacing, weight and structure.
   The injected pricing table keeps its own theme-neutral inline styles; here we only
   round its corners and add a hover cue. */
.tc-panel :deep(h3) { font-size: 1.05rem; font-weight: 700; margin: 0 0 0.5rem; }
.tc-panel :deep(h4) { font-size: 0.9rem; font-weight: 700; margin: 1.25rem 0 0.35rem; }
.tc-panel :deep(p) { margin: 0 0 0.75rem; }
.tc-panel :deep(em) { opacity: 0.7; }
.tc-panel :deep(a) { color: var(--brand-primary); text-decoration: underline; }
.tc-panel :deep(table) {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(128, 128, 128, 0.18);
}
.tc-panel :deep(tbody tr:hover) { background: rgba(128, 128, 128, 0.05); }
</style>
