<template>
  <div
    v-show="show"
    class="fixed z-20 w-80 h-[calc(100%_-_80px)] text-ink-gray-9 m-5 mt-[62px] p-3 flex gap-2 flex-col justify-between rounded-lg bg-surface-modal shadow-2xl"
    :class="[minimize ? 'right-0 top-[calc(100%_-_110px)]' : 'right-0']"
    @click.stop
  >
    <div class="overflow-hidden flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div>
          <div v-if="minimize" class="text-base font-medium ml-1">
            {{ __('Getting started') }}
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
      <div class="flex flex-col justify-center items-center gap-1 mb-3">
        <CRMLogo class="size-10 shrink-0 rounded mb-4" />
        <div class="text-base font-medium">
          {{ __('Welcome to Frappe CRM') }}
        </div>
        <div class="text-p-base font-normal">
          {{ __('{0}/{1} steps completed', [stepsCompleted, totalSteps]) }}
        </div>
      </div>
      <div class="flex flex-col gap-2.5 overflow-hidden">
        <div class="flex justify-between items-center py-0.5">
          <div class="text-base font-medium">{{ __('Getting started') }}</div>
          <Badge
            :label="__('{0}% completed', [completedPercentage])"
            theme="orange"
            size="lg"
          />
        </div>
        <div class="flex flex-col gap-1.5 overflow-y-auto">
          <div
            v-for="step in steps"
            :key="step.title"
            class="w-full flex gap-2 items-center hover:bg-surface-gray-1 rounded px-2 py-1.5 cursor-pointer"
            :class="[
              step.completed
                ? 'text-ink-gray-5 line-through'
                : 'text-ink-gray-8',
            ]"
            @click="step.onClick"
          >
            <component :is="step.icon" class="h-4" />
            <div class="text-base">{{ step.title }}</div>
          </div>
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-1.5">
      <div
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
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { useOnboarding } from '@/composables/onboarding'
import { ref } from 'vue'

const props = defineProps({
  isOnboardingStepsCompleted: Boolean,
})

const show = defineModel()

const { steps, stepsCompleted, totalSteps, completedPercentage, minimize } =
  useOnboarding()
</script>
