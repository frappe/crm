<template>
  <div class="mx-auto w-full max-w-2xl px-4 py-6">
    <h2 class="mb-1 text-xl font-bold text-gray-900 dark:text-white">Your Package Pricing</h2>
    <p class="mb-5 text-sm text-gray-500 dark:text-gray-400">
      Pricing is computed from your KEPH level and locked at your selected rate.
    </p>

    <!-- Loading state -->
    <div v-if="loading" class="py-12 text-center">
      <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-transparent" :style="{ borderTopColor: 'var(--brand-primary)' }" />
      <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">Calculating your pricing...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="errorMsg" class="rounded-xl bg-red-50 px-6 py-8 text-center dark:bg-red-900/10">
      <p class="text-sm text-red-600 dark:text-red-400">{{ errorMsg }}</p>
      <button
        class="mt-3 text-xs underline text-red-600 hover:text-red-800 dark:text-red-400"
        @click="loadPricing"
      >
        Retry
      </button>
    </div>

    <!-- Pricing table -->
    <template v-else-if="pricing">
      <!-- Hero total: the number that matters, made unmissable. Brand-tinted surface +
           accent bar keep it high-contrast on any network brand hue. -->
      <div class="mb-5 flex overflow-hidden rounded-2xl border border-gray-200 shadow-sm dark:border-gray-700">
        <div class="w-1.5 shrink-0" style="background-color: var(--brand-primary)" />
        <div
          class="flex-1 p-5"
          style="background-color: color-mix(in srgb, var(--brand-primary) 6%, transparent)"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Total Monthly · incl. VAT
              </p>
              <p class="mt-0.5 text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                {{ fmtKes(pricing.grand_total_monthly) }}
              </p>
            </div>
            <span
              class="mt-1 shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold"
              style="background-color: color-mix(in srgb, var(--brand-primary) 14%, transparent); color: var(--brand-primary)"
            >
              {{ pricing.facilities.length }} {{ pricing.facilities.length === 1 ? 'facility' : 'facilities' }}
            </span>
          </div>
          <div class="mt-2 flex items-baseline gap-2 text-sm">
            <span class="text-gray-500 dark:text-gray-400">Annual (incl. VAT)</span>
            <span class="font-semibold text-gray-800 dark:text-gray-200">{{ fmtKes(pricing.grand_total_annual) }}</span>
          </div>
        </div>
      </div>

      <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Facility
              </th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                KEPH Level
              </th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Monthly (KES)
              </th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Annual (KES)
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr
              v-for="fac in pricing.facilities"
              :key="fac.mfl_code"
              class="bg-white dark:bg-gray-900"
            >
              <td class="px-4 py-3">
                <p class="font-medium text-gray-900 dark:text-white">{{ fac.facility_name }}</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">{{ fac.mfl_code }}</p>
              </td>
              <td class="px-4 py-3">
                <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', kephBadgeClass(fac.keph_level)]">
                  {{ fac.keph_level }}
                </span>
              </td>
              <td class="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                {{ fmtKes(fac.monthly_kes) }}
              </td>
              <td class="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                {{ fmtKes(fac.annual_kes) }}
              </td>
            </tr>
          </tbody>
          <!-- Subtotals -->
          <tfoot class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <td colspan="2" class="px-4 py-2 text-right text-xs text-gray-500 dark:text-gray-400">Subtotal</td>
              <td class="px-4 py-2 text-right text-sm text-gray-700 dark:text-gray-300">{{ fmtKes(pricing.subtotal_monthly) }}</td>
              <td class="px-4 py-2 text-right text-sm text-gray-700 dark:text-gray-300">{{ fmtKes(pricing.subtotal_annual) }}</td>
            </tr>
            <tr>
              <td colspan="2" class="px-4 py-2 text-right text-xs text-gray-500 dark:text-gray-400">VAT (16%)</td>
              <td class="px-4 py-2 text-right text-sm text-gray-700 dark:text-gray-300">{{ fmtKes(pricing.vat_monthly) }}</td>
              <td class="px-4 py-2 text-right text-sm text-gray-700 dark:text-gray-300">{{ fmtKes(pricing.vat_annual) }}</td>
            </tr>
            <tr class="border-t-2 border-gray-200 dark:border-gray-600">
              <td colspan="2" class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">Grand Total (incl. VAT)</td>
              <td class="px-4 py-3 text-right text-base font-bold" :style="{ color: 'var(--brand-primary)' }">
                {{ fmtKes(pricing.grand_total_monthly) }}
              </td>
              <td class="px-4 py-3 text-right text-base font-bold" :style="{ color: 'var(--brand-primary)' }">
                {{ fmtKes(pricing.grand_total_annual) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p class="mt-3 text-xs text-gray-400 dark:text-gray-500">
        * Prices exclude applicable taxes shown above. All amounts in Kenya Shillings (KES).
      </p>
    </template>

    <!-- Footer nav -->
    <div class="mt-6 flex items-center justify-between">
      <button
        class="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="emit('back')"
      >
        Back
      </button>
      <button
        :disabled="loading || !!errorMsg || !pricing"
        class="rounded-xl px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="emit('continue')"
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
})

const emit = defineEmits(['continue', 'back'])

const store = useOptInStore()
const loading = ref(false)
const errorMsg = ref('')
const pricing = ref(store.pricing || null)

const pricingResource = createResource({ url: 'crm.api.optin.get_pricing' })

async function loadPricing() {
  loading.value = true
  errorMsg.value = ''
  try {
    const mflCodes = (store.selectedFacilities || []).map(f => f.mfl_code)
    const data = await pricingResource.fetch({
      signing_token: store.signingToken,
      email: store.contact.email,
      network_slug: props.networkSlug,
      expiry: store.signingExpiry,
      selected_mfl_codes: JSON.stringify(mflCodes),
    })
    pricing.value = data
    store.setPricing(data)
  } catch (err) {
    errorMsg.value = (err && err.message) ? err.message : 'Failed to load pricing. Please go back and try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!store.pricing) {
    loadPricing()
  }
})

function kephBadgeClass(keph) {
  const level = (keph || '').replace(/^Level\s+/i, '').trim().toUpperCase()
  if (['5', '6'].includes(level)) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  if (['3A', '4', '4B'].includes(level)) return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
  return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
}

function fmtKes(v) {
  const n = parseFloat(v || 0)
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}
</script>
