<template>
  <div class="mx-auto w-full max-w-2xl px-4 py-8">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 dark:text-white">Your Facilities</h2>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Select the facilities you want to register for CareverseHIMS.
        </p>
      </div>
      <div class="flex gap-2">
        <button
          class="text-xs font-medium underline text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          @click="selectAll"
        >
          Select All
        </button>
        <span class="text-gray-300 dark:text-gray-600">|</span>
        <button
          class="text-xs font-medium underline text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          @click="clearAll"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Facility cards grid -->
    <div class="grid gap-3 sm:grid-cols-2">
      <div
        v-for="facility in facilities"
        :key="facility.mfl_code"
        :class="[
          'cursor-pointer rounded-xl border-2 bg-white p-4 transition-all dark:bg-gray-800',
          isSelected(facility.mfl_code)
            ? 'shadow-sm'
            : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600',
        ]"
        :style="isSelected(facility.mfl_code)
          ? 'border-color: var(--brand-primary); background-color: color-mix(in srgb, var(--brand-primary) 5%, transparent)'
          : ''"
        @click="toggleFacility(facility)"
      >
        <!-- Selected indicator -->
        <div class="mb-2 flex items-start justify-between">
          <div
            :class="[
              'flex h-5 w-5 items-center justify-center rounded-full border-2 transition-all',
              isSelected(facility.mfl_code) ? 'border-transparent text-white' : 'border-gray-300 dark:border-gray-600',
            ]"
            :style="isSelected(facility.mfl_code) ? 'background-color: var(--brand-primary)' : ''"
          >
            <svg v-if="isSelected(facility.mfl_code)" class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <!-- KEPH badge -->
          <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', kephBadgeClass(facility.keph_level)]">
            {{ facility.keph_level }}
          </span>
        </div>

        <!-- Facility name -->
        <p class="font-semibold text-gray-900 dark:text-white">{{ facility.facility_name }}</p>
        <p class="mt-0.5 text-xs text-gray-400 dark:text-gray-500">MFL: {{ facility.mfl_code }}</p>
      </div>
    </div>

    <!-- Empty state (should not happen in pre-qualified mode) -->
    <div
      v-if="facilities.length === 0"
      class="rounded-xl border border-gray-200 py-12 text-center dark:border-gray-700"
    >
      <p class="text-sm text-gray-500 dark:text-gray-400">No facilities found for your account.</p>
    </div>

    <!-- Min selection hint -->
    <p v-if="selected.length === 0 && facilities.length > 0" class="mt-3 text-xs text-amber-600 dark:text-amber-400">
      Please select at least one facility to continue.
    </p>

    <!-- Footer nav -->
    <div class="mt-6 flex items-center justify-between">
      <button
        class="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        @click="emit('back')"
      >
        Back
      </button>
      <button
        :disabled="selected.length === 0"
        class="rounded-xl px-6 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        style="background-color: var(--brand-primary)"
        @click="handleContinue"
      >
        Continue ({{ selected.length }} selected)
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useOptInStore } from './useOptInStore.js'

const props = defineProps({
  facilities: { type: Array, default: () => [] },
})

const emit = defineEmits(['continue', 'back'])

const store = useOptInStore()

// Initialise from store (support back navigation)
const selected = ref(
  (store.selectedFacilities || []).map(f => f.mfl_code)
)

function isSelected(mflCode) {
  return selected.value.includes(mflCode)
}

function toggleFacility(facility) {
  const idx = selected.value.indexOf(facility.mfl_code)
  if (idx === -1) {
    selected.value.push(facility.mfl_code)
  } else {
    selected.value.splice(idx, 1)
  }
}

function selectAll() {
  selected.value = props.facilities.map(f => f.mfl_code)
}

function clearAll() {
  selected.value = []
}

function kephBadgeClass(keph) {
  const level = (keph || '').replace(/^Level\s+/i, '').trim().toUpperCase()
  if (['5', '6'].includes(level)) {
    return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
  if (['3A', '4', '4B'].includes(level)) {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
  }
  return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
}

function handleContinue() {
  const selectedFacilities = props.facilities.filter(f => selected.value.includes(f.mfl_code))
  store.setSelectedFacilities(selectedFacilities)
  emit('continue', selectedFacilities)
}
</script>
