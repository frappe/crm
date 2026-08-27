<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-3">
      <div class="h-4 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
      <div class="h-4 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
      <div class="h-4 w-5/6 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
      <div class="h-4 w-full animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
      <div class="h-4 w-2/3 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="loadError" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
      {{ loadError }}
    </div>

    <!-- Contract content -->
    <template v-else>
      <!-- Scroll panel -->
      <div
        ref="scrollPanel"
        class="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-900"
        style="max-height: 65vh; overflow-y: scroll"
        @scroll="onScroll"
      >
        <!-- Contract HTML rendered server-side from T&C template -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div
          class="prose prose-sm max-w-none dark:prose-invert text-gray-800 dark:text-gray-200"
          v-html="contractHtml"
        ></div>
      </div>

      <!-- Scroll hint — this gates the whole flow (you can't sign until you reach
           the bottom), so it must read as an instruction, not a whisper. -->
      <p
        v-if="!reachedBottom"
        class="mt-2 flex items-center justify-center gap-1.5 text-center text-sm font-medium text-gray-600 dark:text-gray-300"
      >
        <svg
          class="h-4 w-4 animate-bounce"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          :style="{ color: 'var(--brand-primary, #bc1823)' }"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
        Scroll to the bottom to continue
      </p>

      <!-- Signatory info -->
      <div class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Signing as</p>
        <p class="mt-0.5 text-base font-semibold text-gray-900 dark:text-white">{{ signatoryName }}</p>
        <p class="text-sm text-gray-600 dark:text-gray-300">{{ signatoryRole }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  signingToken: { type: String, required: true },
  contract: { type: String, required: true },
  role: { type: String, required: true },
})

const emit = defineEmits(['scrolled-to-bottom', 'loaded'])

const loading = ref(true)
const loadError = ref('')
const contractHtml = ref('')
const signatoryName = ref('')
const signatoryRole = ref('')
const contractDate = ref('')
const scrollPanel = ref(null)
const reachedBottom = ref(false)

const getContractResource = createResource({ url: 'crm.api.contracts.get_contract' })

/**
 * Strip document-level tags whose CSS/JS would escape this panel and restyle the
 * page. <style> and <script> blocks are removed outright (contents and all);
 * <html>/<head>/<body> wrappers are unwrapped so their inner body still renders.
 */
function sanitizeContractHtml(raw) {
  return raw
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<\/?(?:html|head|body|meta|link|title)[^>]*>/gi, '')
}

onMounted(async () => {
  try {
    const data = await getContractResource.fetch({
      signing_token: props.signingToken,
      contract: props.contract,
      role: props.role,
    })
    // T&C templates are sometimes authored as full HTML documents. Injected via
    // v-html, any <style>/<script>/<head>/<body> they carry is UNSCOPED and leaks
    // onto the whole page — which can hide the sign controls. Strip document-level
    // tags so only the contract body is rendered, isolated to this panel.
    contractHtml.value = sanitizeContractHtml(data.contract_html || '')
    signatoryName.value = data.signatory_name || ''
    signatoryRole.value = data.signatory_role || props.role
    contractDate.value = data.contract_date || ''
    emit('loaded', {
      signatoryName: signatoryName.value,
      contractDate: contractDate.value,
    })
  } catch (err) {
    loadError.value = err?.message || 'Failed to load contract. Your session may have expired.'
  } finally {
    loading.value = false
    // SF-1: if the contract is shorter than the panel, the scroll event never fires.
    // Check on next tick once the HTML has rendered.
    await nextTick()
    const el = scrollPanel.value
    if (el && !reachedBottom.value && el.scrollHeight <= el.clientHeight + 8) {
      reachedBottom.value = true
      emit('scrolled-to-bottom')
    }
  }
})

function onScroll() {
  if (reachedBottom.value) return
  const el = scrollPanel.value
  if (!el) return
  // Allow 8px tolerance for rounding
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) {
    reachedBottom.value = true
    emit('scrolled-to-bottom')
  }
}
</script>
