<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      :class="[
        currentView
          ? 'text-ink-gray-5 hover:text-ink-gray-7'
          : 'text-ink-gray-7',
      ]"
    >
      {{ __(title || routeName) }}
    </router-link>
    <span
      v-if="currentView"
      class="mx-0.5 text-base text-ink-gray-4"
      aria-hidden="true"
    >
      /
    </span>
    <ViewSelector v-if="currentView" />
  </div>
</template>
<script setup>
import ViewSelector from '@/components/Views/ViewSelector.vue'
import { inject } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: null,
  },
  routeName: {
    type: String,
    required: true,
  },
})

const currentView = inject('currentView')
</script>
