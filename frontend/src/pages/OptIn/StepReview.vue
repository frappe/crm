<template>
  <div class="mx-auto w-full max-w-lg px-4 py-6">
    <h2 class="mb-1 text-xl font-bold text-gray-900 dark:text-white">Review Your Details</h2>
    <p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
      Please confirm the information below before proceeding to Terms &amp; Conditions.
    </p>

    <!-- Contact section -->
    <div class="mb-4 rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Contact</h3>
        <button
          class="text-xs underline"
          :style="{ color: 'var(--brand-primary)' }"
          @click="emit('edit-contact')"
        >
          Edit
        </button>
      </div>
      <div class="space-y-1.5 text-sm">
        <div class="flex gap-2">
          <span class="w-28 flex-shrink-0 text-gray-400 dark:text-gray-500">Name</span>
          <span class="font-medium text-gray-900 dark:text-white">
            {{ [store.contact.first_name, store.contact.last_name].filter(Boolean).join(' ') || '—' }}
          </span>
        </div>
        <div class="flex gap-2">
          <span class="w-28 flex-shrink-0 text-gray-400 dark:text-gray-500">Email</span>
          <span class="font-medium text-gray-900 dark:text-white">{{ store.contact.email || '—' }}</span>
        </div>
        <div v-if="store.contact.mobile_no" class="flex gap-2">
          <span class="w-28 flex-shrink-0 text-gray-400 dark:text-gray-500">Mobile</span>
          <span class="font-medium text-gray-900 dark:text-white">{{ store.contact.mobile_no }}</span>
        </div>
        <div v-if="store.contact.organisation" class="flex gap-2">
          <span class="w-28 flex-shrink-0 text-gray-400 dark:text-gray-500">Organisation</span>
          <span class="font-medium text-gray-900 dark:text-white">{{ store.contact.organisation }}</span>
        </div>
        <div v-if="store.contact.role" class="flex gap-2">
          <span class="w-28 flex-shrink-0 text-gray-400 dark:text-gray-500">Role</span>
          <span class="font-medium text-gray-900 dark:text-white">{{ store.contact.role }}</span>
        </div>
      </div>
    </div>

    <!-- Facility Witness section — the only section on this screen that asks for
         input, so it wears the accent-bar + tint treatment (same shell as the
         Pricing card) to lift it out of the read-only review cards around it.
         Captured here so it flows straight onto the contract the CRM team
         generates later (no chasing the facility for it). -->
    <div class="mb-4 flex overflow-hidden rounded-xl border border-gray-200 shadow-sm dark:border-gray-700">
      <div class="w-1.5 shrink-0" style="background-color: var(--brand-primary)" />
      <div
        class="flex-1 p-5"
        style="background-color: color-mix(in srgb, var(--brand-primary) 6%, transparent)"
      >
        <div class="mb-4">
          <h3
            class="text-sm font-bold uppercase tracking-wider"
            style="color: var(--brand-primary)"
          >
            Facility Witness
          </h3>
          <p class="mt-1 text-sm text-gray-600 dark:text-gray-300">
            A colleague at your facility who will witness the signing of your agreement.
            <span class="font-medium text-gray-700 dark:text-gray-200">Both fields are required.</span>
          </p>
        </div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs font-semibold text-gray-800 dark:text-gray-200">
              Witness Name <span class="text-red-500">*</span>
            </label>
            <input
              v-model="witnessName"
              type="text"
              placeholder="Full legal name"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
              style="--tw-ring-color: var(--brand-primary)"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-semibold text-gray-800 dark:text-gray-200">
              Witness Email <span class="text-red-500">*</span>
            </label>
            <input
              v-model="witnessEmail"
              type="email"
              placeholder="witness@hospital.or.ke"
              :class="['w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-transparent focus:outline-none focus:ring-2 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500',
                witnessEmailError ? 'border-red-400 dark:border-red-600' : 'border-gray-300 dark:border-gray-600']"
              style="--tw-ring-color: var(--brand-primary)"
            />
            <p v-if="witnessEmailError" class="mt-1 text-xs text-red-500">{{ witnessEmailError }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Facilities section -->
    <div class="mb-4 rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-sm font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
          Facilities ({{ store.selectedFacilities.length }})
        </h3>
        <button
          class="text-xs underline"
          :style="{ color: 'var(--brand-primary)' }"
          @click="emit('edit-facilities')"
        >
          Edit
        </button>
      </div>
      <div class="space-y-2">
        <div
          v-for="fac in store.selectedFacilities"
          :key="fac.mfl_code"
          class="flex items-center justify-between text-sm"
        >
          <div>
            <p class="font-medium text-gray-900 dark:text-white">{{ fac.facility_name }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500">MFL: {{ fac.mfl_code }}</p>
          </div>
          <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', kephBadgeClass(fac.keph_level)]">
            {{ fac.keph_level }}
          </span>
        </div>
      </div>
    </div>

    <!-- Pricing summary -->
    <div
      v-if="store.pricing"
      class="mb-6 flex overflow-hidden rounded-xl border border-gray-200 shadow-sm dark:border-gray-700"
    >
      <div class="w-1.5 shrink-0" style="background-color: var(--brand-primary)" />
      <div
        class="flex-1 p-5"
        style="background-color: color-mix(in srgb, var(--brand-primary) 6%, transparent)"
      >
        <div class="mb-2 flex items-center justify-between">
          <h3 class="text-sm font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
            Pricing Summary
          </h3>
          <button
            class="text-xs underline"
            :style="{ color: 'var(--brand-primary)' }"
            @click="emit('edit-facilities')"
          >
            Edit
          </button>
        </div>
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
          Total Monthly · incl. VAT
        </p>
        <p class="mt-0.5 text-2xl font-extrabold tracking-tight text-gray-900 dark:text-white">
          {{ fmtKes(store.pricing.grand_total_monthly) }}
        </p>
        <div class="mt-1.5 flex items-baseline gap-2 text-sm">
          <span class="text-gray-500 dark:text-gray-400">Annual (incl. VAT)</span>
          <span class="font-semibold text-gray-800 dark:text-gray-200">
            {{ fmtKes(store.pricing.grand_total_annual) }}
          </span>
        </div>
        <p class="mt-2 text-xs text-gray-400 dark:text-gray-500">Rates locked at time of submission.</p>
      </div>
    </div>

    <!-- Footer nav -->
    <div class="flex items-center justify-between">
      <button
        class="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="emit('back')"
      >
        Back
      </button>
      <button
        :disabled="!witnessValid"
        class="rounded-xl px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="emit('continue')"
      >
        Continue to Terms &amp; Conditions
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useOptInStore } from './useOptInStore.js'

const emit = defineEmits(['continue', 'back', 'edit-contact', 'edit-facilities'])

const store = useOptInStore()

// Witness fields write straight through to the store so the value survives
// back-nav and rides along in the submit payload (StepCommit).
const witnessName = computed({
  get: () => store.witness.name,
  set: (val) => store.setWitness({ name: val }),
})
const witnessEmail = computed({
  get: () => store.witness.email,
  set: (val) => store.setWitness({ email: val }),
})

function validEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

const witnessEmailError = computed(() => {
  const email = (store.witness.email || '').trim()
  if (!email) return ''
  return validEmail(email) ? '' : 'Please enter a valid email address.'
})

const witnessValid = computed(
  () => (store.witness.name || '').trim() !== '' && validEmail((store.witness.email || '').trim())
)

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
