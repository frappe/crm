<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-10 dark:bg-gray-950">
    <div class="w-full max-w-lg text-center">
      <!-- Network logo or default Tiberbu logo -->
      <div class="mb-7 flex justify-center">
        <img
          v-if="networkConfig && networkConfig.logo_url"
          :src="networkConfig.logo_url"
          :alt="networkConfig.display_name || 'Network logo'"
          class="h-16 w-auto object-contain"
        />
        <div
          v-else
          class="flex h-16 w-16 items-center justify-center rounded-2xl"
          style="background-color: var(--brand-primary)"
        >
          <span class="text-2xl font-black text-white">C</span>
        </div>
      </div>

      <!-- Headline -->
      <h1 class="mb-3 text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white">
        {{ networkConfig ? networkConfig.display_name : 'CareverseHIMS' }}
      </h1>

      <!-- Subheadline -->
      <p class="mb-8 text-base text-gray-500 dark:text-gray-400">
        Register your facilities for CareverseHIMS and get set up online — start to
        finish, without a single phone call.
      </p>

      <!-- What you're starting: explained value props -->
      <div class="mb-9 space-y-3 text-left">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="flex items-start gap-3.5 rounded-xl border border-gray-100 bg-white p-4 dark:border-gray-800 dark:bg-gray-900"
        >
          <span
            class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            :style="{ backgroundColor: brandTint }"
          >
            <span class="h-5 w-5" style="color: var(--brand-primary)" v-html="feature.icon" />
          </span>
          <div>
            <p class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ feature.title }}
            </p>
            <p class="mt-0.5 text-[13px] leading-snug text-gray-500 dark:text-gray-400">
              {{ feature.body }}
            </p>
          </div>
        </div>
      </div>

      <!-- CTA button -->
      <button
        class="w-full rounded-xl px-6 py-3.5 text-base font-semibold text-white shadow-lg transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2"
        style="background-color: var(--brand-primary); --tw-ring-color: var(--brand-primary)"
        @click="emit('next')"
      >
        Get Started
      </button>

      <!-- Partner logos strip -->
      <div v-if="partnerLogos.length" class="mt-10">
        <p class="mb-4 text-xs font-medium uppercase tracking-wide text-gray-400 dark:text-gray-500">
          Trusted by our partners
        </p>
        <div class="flex flex-wrap items-center justify-center gap-x-7 gap-y-4">
          <component
            :is="partner.website ? 'a' : 'div'"
            v-for="partner in partnerLogos"
            :key="partner.partner_name + partner.logo"
            :href="partner.website || undefined"
            :target="partner.website ? '_blank' : undefined"
            :rel="partner.website ? 'noopener noreferrer' : undefined"
            class="inline-flex items-center"
          >
            <img
              :src="partner.logo"
              :alt="partner.partner_name || 'Partner'"
              :title="partner.partner_name || ''"
              class="h-8 w-auto max-w-[140px] object-contain opacity-60 grayscale transition hover:opacity-100 hover:grayscale-0 dark:opacity-70"
            />
          </component>
        </div>
      </div>

      <!-- Footer legal name -->
      <p
        v-if="networkConfig && networkConfig.footer_legal_name"
        class="mt-8 text-xs text-gray-400 dark:text-gray-600"
      >
        in partnership with {{ networkConfig.footer_legal_name }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  networkConfig: { type: Object, default: null },
})

const emit = defineEmits(['next'])

// Partner logos supplied by the network config (crm.api.optin.get_settings).
const partnerLogos = computed(() => props.networkConfig?.partner_logos || [])

// Soft brand-tinted background for the feature icons. Falls back to a neutral
// tint when the network has no primary colour so it never reads as "off-brand".
const brandTint = computed(() => {
  const hex = props.networkConfig?.primary_colour
  if (typeof hex === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(hex.trim())) {
    const v = hex.trim().slice(1)
    const full = v.length === 3 ? v.split('').map((c) => c + c).join('') : v
    const r = parseInt(full.slice(0, 2), 16)
    const g = parseInt(full.slice(2, 4), 16)
    const b = parseInt(full.slice(4, 6), 16)
    return `rgba(${r}, ${g}, ${b}, 0.1)`
  }
  return 'rgba(192, 16, 26, 0.1)'
})

// Expanded value propositions — each pill from the old landing, now explained so
// the user understands what they're starting before they commit.
const features = [
  {
    title: 'Auto-priced by KEPH level',
    body: 'Your subscription price is calculated automatically from each facility’s KEPH level. No quotes to chase, no negotiation.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="100%" height="100%"><path d="M20.59 13.41 13.42 20.58a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
  },
  {
    title: 'No sales call needed',
    body: 'Complete everything online at your own pace — no meetings, no phone tag, no waiting on a sales rep to get back to you.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="100%" height="100%"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><polyline points="8.5 10.5 11 13 15.5 8.5"/></svg>',
  },
  {
    title: 'Under 5 minutes',
    body: 'Verify your email, pick your facilities, review the pricing and accept. Most facilities finish the whole thing in under five minutes.',
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="100%" height="100%"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  },
]
</script>
