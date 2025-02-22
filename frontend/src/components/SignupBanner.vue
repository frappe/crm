<template>
  <div
    v-if="!isSidebarCollapsed && showBanner"
    class="m-2 flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-white text-base"
  >
    <div class="flex flex-col gap-1">
      <div class="inline-flex gap-2 items-center font-medium">
        <FeatherIcon class="h-4" name="info" />
        {{ __('Loved the demo?') }}
      </div>
      <div class="text-ink-gray-7 text-p-sm">
        {{ __('Try Frappe CRM for free with a 14-day trial.') }}
      </div>
    </div>
    <Button :label="__('Sign up now')" theme="blue" @click="signupNow">
      <template #prefix>
        <LightningIcon class="size-4" />
      </template>
    </Button>
  </div>
</template>
<script setup>
import LightningIcon from '@/components/Icons/LightningIcon.vue'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const showBanner = ref(window.is_demo_site)

function signupNow() {
  capture('signup_from_demo_site')
  window.open('https://frappecrm.ru/ru/contact/', '_blank')
}
</script>
