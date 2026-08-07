<template>
  <!-- Full-screen quote builder overlay -->
  <div
    class="fixed inset-0 z-50 flex flex-col bg-white dark:bg-gray-950 overflow-hidden"
    style="animation: slideUp 0.2s ease-out;"
  >
    <!-- Top bar -->
    <div class="flex h-14 flex-shrink-0 items-center justify-between border-b border-outline-elevation-2 px-5">
      <button
        class="flex items-center gap-1.5 text-sm text-ink-gray-6 hover:text-ink-gray-9 transition-colors"
        @click="handleBack"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        {{ __('Back') }}
      </button>
      <div class="flex items-center gap-3">
        <span class="text-sm font-semibold text-ink-gray-9">
          {{ quoteName ? quoteName : __('New Quote') }}
        </span>
        <!-- Step progress -->
        <div class="hidden items-center gap-1 sm:flex">
          <div
            v-for="(step, i) in steps"
            :key="step"
            class="flex items-center gap-1"
          >
            <div
              :class="[
                'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold transition-colors',
                i < currentStep
                  ? 'bg-green-500 text-white'
                  : i === currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-surface-gray-3 text-ink-gray-4',
              ]"
            >
              <svg v-if="i < currentStep" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <span class="text-xs" :class="i === currentStep ? 'font-medium text-ink-gray-9' : 'text-ink-gray-4'">{{ __(step) }}</span>
            <svg v-if="i < steps.length - 1" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-ink-gray-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </div>
      </div>
      <Button size="sm" variant="subtle" :loading="saving" @click="saveDraft">{{ __('Save Draft') }}</Button>
    </div>

    <!-- Step content -->
    <div class="flex-1 overflow-y-auto">
      <QuoteStep1Facilities
        v-if="currentStep === 0"
        v-model:facilities="quoteData.facilities"
        :context="context"
        @next="currentStep = 1"
        @dirty="isDirty = true"
      />
      <QuoteStep2Addons
        v-else-if="currentStep === 1"
        v-model:addons="quoteData.addons"
        @back="currentStep = 0"
        @next="currentStep = 2"
        @dirty="isDirty = true"
      />
      <QuoteStep3Pricing
        v-else-if="currentStep === 2"
        v-model:payment-terms="quoteData.payment_terms"
        v-model:contract-term-yrs="quoteData.contract_term_yrs"
        v-model:saas-discount="quoteData.saas_discount"
        v-model:services-discount="quoteData.services_discount"
        :facilities="quoteData.facilities"
        :addons="quoteData.addons"
        :context="context"
        @back="currentStep = 1"
        @next="currentStep = 3"
        @dirty="isDirty = true"
      />
      <QuoteStep4Review
        v-else-if="currentStep === 3"
        :quote-data="quoteData"
        :quote-name="currentQuoteName"
        :context="context"
        :deal-id="dealId"
        @back="currentStep = 2"
        @saved="onSaved"
        @sent="onSaved"
        @accepted="onAccepted"
        @rejected="onSaved"
      />
    </div>

    <!-- Unsaved-changes dialog -->
    <Dialog
      v-model="showDirtyDialog"
      :options="{ title: __('Save draft before leaving?'), size: 'sm' }"
    >
      <template #body-content>
        <p class="text-sm text-ink-gray-6">{{ __('You have unsaved changes.') }}</p>
      </template>
      <template #actions>
        <Button variant="subtle" @click="discardAndClose">{{ __('Discard Changes') }}</Button>
        <Button variant="solid" :loading="saving" @click="saveDraftAndClose">{{ __('Save Draft') }}</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { Button, Dialog } from 'frappe-ui'
import QuoteStep1Facilities from './steps/QuoteStep1Facilities.vue'
import QuoteStep2Addons from './steps/QuoteStep2Addons.vue'
import QuoteStep3Pricing from './steps/QuoteStep3Pricing.vue'
import QuoteStep4Review from './steps/QuoteStep4Review.vue'

const props = defineProps({
  dealId:    { type: String, required: true },
  quoteName: { type: String, default: null },
})
const emit = defineEmits(['close', 'saved'])

const steps = ['Facilities', 'Add-ons', 'Pricing', 'Review']
const currentStep = ref(0)
const isDirty = ref(false)
const saving = ref(false)
const showDirtyDialog = ref(false)
const currentQuoteName = ref(props.quoteName || null)

const quoteData = reactive({
  deal: props.dealId,
  payment_terms: 'Annual Upfront',
  contract_term_yrs: 1,
  saas_discount: 0,
  services_discount: 0,
  facilities: [],
  addons: [],
})

// Load context (partner tier, max discounts, customer)
const contextResource = createResource({
  url: 'crm.api.quotes.get_quote_context',
  makeParams: () => ({ deal: props.dealId }),
  auto: true,
})
const context = ref({})
onMounted(async () => {
  await contextResource.fetch()
  context.value = contextResource.data || {}

  // If editing existing quote, load its data
  if (props.quoteName) {
    const pdfData = createResource({
      url: 'crm.api.quotes.get_quote_pdf_data',
      makeParams: () => ({ quote_name: props.quoteName }),
      auto: true,
    })
    await pdfData.fetch()
    if (pdfData.data) {
      const d = pdfData.data
      quoteData.payment_terms = d.payment_terms || 'Annual Upfront'
      quoteData.contract_term_yrs = d.contract_term_yrs || 1
      quoteData.facilities = (d.facilities || []).map(f => ({ ...f }))
      quoteData.addons = (d.addons || []).map(a => ({ ...a }))
      currentStep.value = 3 // Open in Review for existing quotes
    }
  }
})

function handleBack() {
  if (isDirty.value) {
    showDirtyDialog.value = true
  } else {
    emit('close')
  }
}

async function saveDraft() {
  saving.value = true
  try {
    const saveResource = createResource({ url: 'crm.api.quotes.save_quote' })
    const payload = {
      ...quoteData,
      name: currentQuoteName.value,
      status: 'Draft',
    }
    const result = await saveResource.submit({ quote_data: JSON.stringify(payload) })
    currentQuoteName.value = result.name
    isDirty.value = false
  } finally {
    saving.value = false
  }
}

async function saveDraftAndClose() {
  await saveDraft()
  showDirtyDialog.value = false
  emit('saved')
}

function discardAndClose() {
  showDirtyDialog.value = false
  isDirty.value = false
  emit('close')
}

function onSaved() {
  isDirty.value = false
  emit('saved')
}

function onAccepted() {
  isDirty.value = false
  emit('saved')
}
</script>

<style scoped>
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
</style>
