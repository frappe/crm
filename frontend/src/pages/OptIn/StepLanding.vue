<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 dark:bg-gray-950">
    <div class="w-full max-w-md text-center">
      <!-- Network logo or default Tiberbu logo -->
      <div class="mb-8 flex justify-center">
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
        Register your facilities in minutes
      </p>

      <!-- Value proposition pills -->
      <div class="mb-10 flex flex-wrap justify-center gap-2">
        <span class="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
          Auto-priced by KEPH level
        </span>
        <span class="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
          No sales call needed
        </span>
        <span class="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
          Under 5 minutes
        </span>
      </div>

      <!-- CTA button -->
      <button
        class="w-full rounded-xl px-6 py-3.5 text-base font-semibold text-white shadow-lg transition-opacity hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2"
        style="background-color: var(--brand-primary); --tw-ring-color: var(--brand-primary)"
        @click="emit('next')"
      >
        Get Started
      </button>

      <!-- Footer legal name -->
      <p
        v-if="networkConfig && networkConfig.footer_legal_name"
        class="mt-6 text-xs text-gray-400 dark:text-gray-600"
      >
        in partnership with {{ networkConfig.footer_legal_name }}
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  networkConfig: { type: Object, default: null },
})

const emit = defineEmits(['next'])
</script>
