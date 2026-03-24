<template>
  <div
    v-if="!isSidebarCollapsed"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-white text-base"
  >
    <div class="flex flex-col gap-1">
      <slot>
        <div class="inline-flex gap-2 items-center font-medium">
          <FeatherIcon class="h-4" name="info" />
          {{ __('Loved the demo?') }}
        </div>
        <div class="text-ink-gray-7 text-p-sm">
          {{ __('Try {0} for free with a 14-day trial.', [appName]) }}
        </div>
      </slot>
    </div>
    <Button :label="__('Sign up now')" theme="blue" @click="signupNow">
      <template #prefix>
        <LightningIcon class="size-4" />
      </template>
    </Button>
  </div>
  <Button v-else @click="signupNow">
    <LightningIcon class="h-4 my-0.5 shrink-0" />
  </Button>
</template>

<script setup>
import LightningIcon from '@/components/Icons/LightningIcon.vue'
import { Button, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
  appName: {
    type: String,
    default: 'Frappe CRM',
  },
  redirectURL: {
    type: String,
    default: 'https://frappecloud.com/crm/signup',
  },
  afterSignup: {
    type: Function,
    default: () => {},
  },
})

function signupNow() {
  window.open(props.redirectURL, '_blank')
  props.afterSignup?.()
}
</script>
