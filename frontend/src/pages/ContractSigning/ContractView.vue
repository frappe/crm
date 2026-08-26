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

      <!-- Scroll hint -->
      <p
        v-if="!reachedBottom"
        class="mt-2 text-center text-xs text-gray-400 dark:text-gray-500"
      >
        Scroll to the bottom to continue
      </p>

      <!-- Signatory info -->
      <div class="mt-4 rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400">Signing as</p>
        <p class="mt-0.5 text-sm font-semibold text-gray-900 dark:text-white">{{ signatoryName }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">{{ signatoryRole }}</p>
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

onMounted(async () => {
  try {
    const data = await getContractResource.fetch({
      signing_token: props.signingToken,
      contract: props.contract,
      role: props.role,
    })
    contractHtml.value = data.contract_html || ''
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
