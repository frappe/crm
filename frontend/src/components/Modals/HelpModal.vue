<template>
  <div
    v-show="show"
    class="fixed z-20 w-80 h-[calc(100%_-_80px)] text-ink-gray-9 m-5 mt-[62px] p-3 flex gap-2 flex-col justify-between rounded-lg bg-surface-modal shadow-2xl"
    :class="[minimize ? 'right-0 top-[calc(100%_-_110px)]' : 'right-0']"
    @click.stop
  >
    <div class="flex items-center justify-between">
      <div class="text-base font-medium ml-1">
        <div v-if="minimize && !isOnboardingStepsCompleted">
          {{ __('Getting started') }}
        </div>
        <div v-else>
          {{ __('Help center') }}
        </div>
      </div>
      <div>
        <Button @click="minimize = !minimize" variant="ghost">
          <component
            :is="minimize ? MaximizeIcon : MinimizeIcon"
            class="h-3.5"
          />
        </Button>
        <Button variant="ghost" @click="show = false">
          <FeatherIcon name="x" class="h-3.5" />
        </Button>
      </div>
    </div>
    <div class="h-full overflow-hidden flex flex-col">
      <OnboardingSteps v-if="!isOnboardingStepsCompleted" />
    </div>
    <div class="flex flex-col gap-1.5">
      <div
        v-if="!isOnboardingStepsCompleted"
        class="w-full flex gap-2 items-center hover:bg-surface-gray-1 text-ink-gray-8 rounded px-2 py-1.5 cursor-pointer"
      >
        <HelpIcon class="h-4" />
        <div class="text-base">{{ __('Help centre') }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import MaximizeIcon from '@/components/Icons/MaximizeIcon.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import OnboardingSteps from '@/components/OnboardingSteps.vue'
import { isOnboardingStepsCompleted, minimize } from '@/composables/onboarding'

const show = defineModel()
</script>
