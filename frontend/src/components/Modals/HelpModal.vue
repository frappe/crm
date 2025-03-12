<template>
  <div
    v-show="show"
    class="fixed z-20 w-80 h-[calc(100%_-_80px)] text-ink-gray-9 m-5 mt-[62px] p-3 flex gap-2 flex-col justify-between rounded-lg bg-surface-modal shadow-2xl"
    :class="[minimize ? 'right-0 top-[calc(100%_-_110px)]' : 'right-0']"
    @click.stop
  >
    <div class="flex items-center justify-between">
      <div class="text-base font-medium ml-1">
        {{ __(title) }}
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
      <OnboardingSteps v-if="!isOnboardingStepsCompleted && !showHelpCenter" />
    </div>
    <div v-for="item in footerItems" class="flex flex-col gap-1.5">
      <div
        class="w-full flex gap-2 items-center hover:bg-surface-gray-1 text-ink-gray-8 rounded px-2 py-1.5 cursor-pointer"
        @click="item.onClick"
      >
        <component :is="item.icon" class="h-4" />
        <div class="text-base">{{ __(item.label) }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import MaximizeIcon from '@/components/Icons/MaximizeIcon.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import OnboardingSteps from '@/components/OnboardingSteps.vue'
import {
  isOnboardingStepsCompleted,
  minimize,
  useOnboarding,
} from '@/composables/onboarding'
import { onMounted, computed } from 'vue'

const show = defineModel()
const showHelpCenter = ref(false)

const title = computed(() => {
  if (!isOnboardingStepsCompleted.value && !showHelpCenter.value) {
    return __('Getting started')
  } else if (showHelpCenter.value) {
    return __('Help center')
  }
})

const footerItems = computed(() => {
  let items = [
    {
      icon: HelpIcon,
      label: __('Help centre'),
      onClick: () => {
        showHelpCenter.value = true
      },
      condition: !isOnboardingStepsCompleted.value && !showHelpCenter.value,
    },
    {
      icon: StepsIcon,
      label: __('Getting started'),
      onClick: () => (showHelpCenter.value = false),
      condition: showHelpCenter.value && !isOnboardingStepsCompleted.value,
    },
    {
      icon: StepsIcon,
      label: __('Reset onboarding steps'),
      onClick: resetOnboardingSteps,
      condition: showHelpCenter.value && isOnboardingStepsCompleted.value,
    },
  ]

  return items.filter((item) => item.condition)
})

function resetOnboardingSteps() {
  const { reset } = useOnboarding()
  reset()
  isOnboardingStepsCompleted.value = false
  showHelpCenter.value = false
}

onMounted(() => {
  if (isOnboardingStepsCompleted.value) {
    showHelpCenter.value = true
  }
})
</script>
