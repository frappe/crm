<template>
  <div class="mx-auto max-w-3xl px-5 py-6">
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Configure Facilities') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('Add one row per facility or branch. Each row becomes a separate line on the quote.') }}</p>
    </div>

    <div class="grid gap-5 lg:grid-cols-[1fr_280px]">
      <!-- Facility cards -->
      <div class="space-y-4">
        <div
          v-for="(facility, idx) in facilities"
          :key="idx"
          class="rounded-xl border border-outline-elevation-2 bg-surface-white p-4 dark:bg-surface-gray-1"
        >
          <!-- Facility name -->
          <div class="mb-3">
            <label class="mb-1 block text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Facility Name') }}</label>
            <input
              v-model="facility.facility_name"
              type="text"
              :placeholder="__('e.g. Main Campus')"
              class="w-full rounded-lg border border-outline-elevation-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:border-blue-500 focus:outline-none dark:bg-surface-gray-2"
              @input="emit('dirty')"
            />
            <p v-if="duplicateName(facility.facility_name, idx)" class="mt-1 text-xs text-amber-600">
              {{ __('⚠ Duplicate facility name') }}
            </p>
          </div>

          <!-- Tier pills -->
          <div class="mb-3">
            <label class="mb-2 block text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Package Tier') }}</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tier in TIERS"
                :key="tier.key"
                :class="[
                  'flex flex-col items-start rounded-lg border-2 px-3 py-2 text-left transition-all',
                  facility.package_tier === tier.key
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-outline-elevation-2 hover:border-blue-300 bg-surface-white dark:bg-surface-gray-2',
                ]"
                @click="selectTier(facility, tier.key)"
              >
                <span class="text-sm font-semibold text-ink-gray-9">{{ tier.key }}</span>
                <span class="text-xs text-ink-gray-4">{{ tier.users }}</span>
                <span class="mt-0.5 text-xs font-medium text-ink-gray-6">{{ fmtKes(tier.subscription) }}/yr</span>
              </button>
            </div>
          </div>

          <!-- Num users -->
          <div class="mb-3">
            <label class="mb-1 block text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ __('Number of Users') }}</label>
            <input
              v-model.number="facility.num_users"
              type="number"
              :min="tierMin(facility.package_tier)"
              :max="tierMax(facility.package_tier)"
              class="w-32 rounded-lg border border-outline-elevation-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 focus:border-blue-500 focus:outline-none dark:bg-surface-gray-2"
              @input="emit('dirty')"
            />
            <p v-if="facility.num_users && !validUsers(facility)" class="mt-1 text-xs text-red-500">
              {{ tierRangeMsg(facility.package_tier) }}
            </p>
          </div>

          <!-- Footer totals -->
          <div class="flex items-center justify-between rounded-lg bg-surface-gray-1 px-3 py-2 text-xs dark:bg-surface-gray-2">
            <span class="text-ink-gray-5">{{ __('Subscription') }}: <strong>{{ fmtKes(tierPrices(facility.package_tier).subscription) }}</strong></span>
            <span class="text-ink-gray-5">{{ __('Impl') }}: <strong>{{ fmtKes(tierPrices(facility.package_tier).impl) }}</strong></span>
            <span class="font-semibold text-ink-gray-9">{{ __('Line Total') }}: {{ fmtKes(lineTotal(facility)) }}</span>
            <button
              :disabled="facilities.length <= 1"
              class="ml-3 text-red-500 disabled:opacity-30 hover:text-red-700 transition-colors"
              @click="removeFacility(idx)"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
            </button>
          </div>
        </div>

        <Button variant="ghost" class="w-full" @click="addFacility">
          <template #prefix>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </template>
          {{ __('+ Add Facility') }}
        </Button>
      </div>

      <!-- Sticky sidebar -->
      <div class="hidden lg:block">
        <div class="sticky top-5 rounded-xl border border-outline-elevation-2 bg-surface-white p-4 dark:bg-surface-gray-1">
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">{{ __('Running Subtotal') }}</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-ink-gray-6">{{ __('Subscription') }}</span>
              <span class="font-medium text-ink-gray-9">{{ fmtKes(subscriptionTotal) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-ink-gray-6">{{ __('Implementation') }}</span>
              <span class="font-medium text-ink-gray-9">{{ fmtKes(implTotal) }}</span>
            </div>
            <div class="my-2 border-t border-outline-elevation-2" />
            <div class="flex justify-between font-semibold">
              <span class="text-ink-gray-9">{{ __('Subtotal') }}</span>
              <span class="text-ink-gray-9">{{ fmtKes(subscriptionTotal + implTotal) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile subtotal footer -->
    <div class="fixed bottom-0 left-0 right-0 flex items-center justify-between border-t border-outline-elevation-2 bg-surface-white px-4 py-3 lg:hidden dark:bg-surface-gray-1">
      <span class="text-sm font-semibold text-ink-gray-9">{{ __('Subtotal') }}: {{ fmtKes(subscriptionTotal + implTotal) }}</span>
      <Button variant="solid" :disabled="!canProceed" @click="emit('next')">{{ __('Continue →') }}</Button>
    </div>

    <!-- Desktop footer nav -->
    <div class="mt-6 hidden items-center justify-end lg:flex">
      <Button variant="solid" :disabled="!canProceed" @click="emit('next')">
        {{ __('Continue → Add-ons') }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps({
  facilities: { type: Array, default: () => [] },
  context:    { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:facilities', 'next', 'dirty'])

const TIERS = [
  { key: 'Core',       users: '1–10 users',    subscription: 605149.06,  impl: 620000.00  },
  { key: 'Advanced',   users: '11–20 users',   subscription: 1821349.83, impl: 1870000.00 },
  { key: 'Enterprise', users: '21–130 users',  subscription: 6044783.95, impl: 6180000.00 },
]

const TIER_RANGES = { Core: [1, 10], Advanced: [11, 20], Enterprise: [21, 130] }

function tierPrices(tier) {
  return TIERS.find(t => t.key === tier) || TIERS[0]
}
function tierMin(tier)  { return (TIER_RANGES[tier] || [1, 10])[0] }
function tierMax(tier)  { return (TIER_RANGES[tier] || [1, 10])[1] }
function validUsers(f)  { const [mn, mx] = TIER_RANGES[f.package_tier] || [1, 10]; return f.num_users >= mn && f.num_users <= mx }
function tierRangeMsg(tier) { const [mn, mx] = TIER_RANGES[tier] || [1,10]; return `${tier} tier supports ${mn}–${mx} users` }

function lineTotal(f) {
  const p = tierPrices(f.package_tier)
  return p.subscription + p.impl
}

function fmtKes(v) {
  if (!v && v !== 0) return 'KES 0'
  const n = parseFloat(v)
  if (n >= 1_000_000) return 'KES ' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return 'KES ' + Math.round(n / 1_000) + 'K'
  return 'KES ' + n.toLocaleString()
}

function duplicateName(name, idx) {
  if (!name) return false
  return props.facilities.some((f, i) => i !== idx && f.facility_name === name)
}

function selectTier(facility, tier) {
  facility.package_tier = tier
  facility.subscription_discount = 0
  facility.impl_discount = 0
  emit('dirty')
}

function addFacility() {
  emit('update:facilities', [
    ...props.facilities,
    { facility_name: '', package_tier: 'Core', num_users: 5, subscription_discount: 0, impl_discount: 0 },
  ])
  emit('dirty')
}

function removeFacility(idx) {
  const updated = props.facilities.filter((_, i) => i !== idx)
  emit('update:facilities', updated)
  emit('dirty')
}

const subscriptionTotal = computed(() =>
  props.facilities.reduce((s, f) => s + (tierPrices(f.package_tier).subscription || 0), 0)
)
const implTotal = computed(() =>
  props.facilities.reduce((s, f) => s + (tierPrices(f.package_tier).impl || 0), 0)
)

const canProceed = computed(() =>
  props.facilities.length > 0 &&
  props.facilities.every(f => f.facility_name && f.package_tier && f.num_users && validUsers(f))
)
</script>
