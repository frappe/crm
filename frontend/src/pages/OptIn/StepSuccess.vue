<template>
  <div class="mx-auto w-full max-w-sm px-4 py-8 text-center">
    <!-- Celebration icon -->
    <div class="mb-6 flex justify-center">
      <div
        class="flex h-16 w-16 items-center justify-center rounded-full"
        style="background-color: var(--brand-primary)"
      >
        <svg class="h-8 w-8 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
    </div>

    <h1 class="mb-2 text-2xl font-extrabold text-gray-900 dark:text-white">You're in!</h1>

    <!-- Reference number -->
    <div class="mb-5 inline-block rounded-lg bg-gray-100 px-4 py-2 dark:bg-gray-800">
      <p class="text-xs text-gray-400 dark:text-gray-500">Reference Number</p>
      <p class="mt-0.5 font-mono text-lg font-bold text-gray-900 dark:text-white">
        {{ store.submissionRef }}
      </p>
    </div>

    <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
      A CRM executive will send your contract shortly. Keep this reference number for your records.
    </p>

    <!-- Facility recap -->
    <div class="mb-6 rounded-xl border border-gray-200 bg-white p-4 text-left dark:border-gray-700 dark:bg-gray-800">
      <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
        Registered Facilities
      </p>
      <div class="space-y-2">
        <div
          v-for="fac in store.selectedFacilities"
          :key="fac.mfl_code"
          class="flex items-center justify-between text-sm"
        >
          <div>
            <p class="font-medium text-gray-900 dark:text-white">{{ fac.facility_name }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500">{{ fac.mfl_code }}</p>
          </div>
          <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', kephBadgeClass(fac.keph_level)]">
            {{ fac.keph_level }}
          </span>
        </div>
      </div>
    </div>

    <!-- Grand total confirmed -->
    <div v-if="store.pricing" class="mb-6 rounded-xl px-5 py-4 text-center" style="background-color: color-mix(in srgb, var(--brand-primary) 8%, transparent)">
      <p class="text-xs text-gray-500 dark:text-gray-400">Monthly commitment (incl. VAT)</p>
      <p class="mt-1 text-2xl font-black" :style="{ color: 'var(--brand-primary)' }">
        {{ fmtKes(store.pricing.grand_total_monthly) }}
      </p>
    </div>

    <!-- Next steps -->
    <div class="text-sm text-gray-400 dark:text-gray-500">
      <p>What happens next:</p>
      <ol class="mt-2 list-decimal space-y-1 pl-5 text-left">
        <li>A CRM executive reviews your submission</li>
        <li>You receive a contract to sign digitally</li>
        <li>Your CareverseHIMS platform is provisioned</li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { useOptInStore } from './useOptInStore.js'

const store = useOptInStore()

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
