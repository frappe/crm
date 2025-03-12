<template>
  <div
    v-if="!isSidebarCollapsed"
    class="m-2 flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-white text-base"
  >
    <div v-if="stepsCompleted != totalSteps" class="inline-flex gap-2">
      <StepsIcon class="h-4 my-0.5 shrink-0" />
      <div class="flex flex-col text-p-sm gap-0.5">
        <div class="text-ink-gray-9 font-medium">
          {{ __('Gettings started') }}
        </div>
        <div class="text-ink-gray-7">
          {{ __('{0}/{1} steps', [stepsCompleted, totalSteps]) }}
        </div>
      </div>
    </div>
    <div v-else class="flex flex-col gap-1">
      <div class="flex items-center justify-between gap-1">
        <div class="flex items-center gap-2 shrink-0">
          <StepsIcon class="h-4 my-0.5" />
          <div class="text-ink-gray-9 font-medium">
            {{ __('You are all set!') }}
          </div>
        </div>
        <FeatherIcon
          name="x"
          class="h-4 cursor-pointer"
          @click="isOnboardingStepsCompleted = true"
        />
      </div>
      <div class="text-p-sm text-ink-gray-7">
        {{ __('All steps are completed successfully!') }}
      </div>
    </div>
    <Button
      v-if="stepsCompleted != totalSteps"
      :label="__('Complete now')"
      theme="blue"
      @click="emit('completeNow')"
    />
  </div>
</template>
<script setup>
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import {
  isOnboardingStepsCompleted,
  useOnboarding,
} from '@/composables/onboarding'
import FeatherIcon from 'frappe-ui/src/components/FeatherIcon.vue'

const props = defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['completeNow'])

const { stepsCompleted, totalSteps } = useOnboarding()
</script>
