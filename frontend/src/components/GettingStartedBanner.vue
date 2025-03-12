<template>
  <div
    v-if="!isSidebarCollapsed"
    class="m-2 flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-white text-base"
  >
    <div class="inline-flex gap-2">
      <StepsIcon class="h-4 my-0.5" />
      <div class="flex flex-col text-p-sm gap-0.5">
        <div class="text-ink-gray-9 font-medium">
          {{ __('Gettings started') }}
        </div>
        <div class="text-ink-gray-7">
          {{ __('{0}/{1} steps', [stepsCompleted, totalSteps]) }}
        </div>
      </div>
    </div>
    <Button
      :label="__('Complete now')"
      theme="blue"
      @click="emit('completeNow')"
    />
  </div>
</template>
<script setup>
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import { useOnboarding } from '@/composables/onboarding'

const props = defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['completeNow'])

const { stepsCompleted, totalSteps } = useOnboarding()
</script>
