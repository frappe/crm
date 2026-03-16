<template>
  <div class="flex flex-col justify-center items-center gap-1 mt-4 mb-7">
    <component :is="logo" class="size-10 shrink-0 rounded mb-4" />
    <div class="text-base font-medium">
      {{ __('Welcome to {0}', [title]) }}
    </div>
    <div class="text-p-base font-normal">
      {{ __('{0}/{1} steps completed', [stepsCompleted, totalSteps]) }}
    </div>
  </div>
  <div class="flex flex-col gap-2.5 overflow-hidden">
    <div class="flex justify-between items-center py-0.5">
      <Badge
        :label="__('{0}% completed', [completedPercentage])"
        :theme="completedPercentage == 100 ? 'green' : 'orange'"
        size="lg"
      />
      <div class="flex">
        <Button
          v-if="completedPercentage != 0"
          variant="ghost"
          :label="__('Reset all')"
          @click="() => resetAll(afterResetAll)"
        />
        <Button
          v-if="completedPercentage != 100"
          variant="ghost"
          :label="__('Skip all')"
          @click="() => skipAll(afterSkipAll)"
        />
      </div>
    </div>
    <div class="flex flex-col gap-1.5 overflow-y-auto">
      <div
        v-for="step in steps"
        :key="step.title"
        class="group w-full flex gap-2 justify-between items-center hover:bg-surface-gray-1 rounded px-2 py-1.5 cursor-pointer"
        @click.stop="
          () => !step.completed && !isDependent(step) && step.onClick()
        "
      >
        <component
          :is="isDependent(step) ? Tooltip : 'div'"
          :text="dependsOnTooltip(step)"
        >
          <div
            class="flex gap-2 items-center"
            :class="[
              step.completed
                ? 'text-ink-gray-5'
                : isDependent(step)
                  ? 'text-ink-gray-4'
                  : 'text-ink-gray-8',
            ]"
          >
            <component :is="step.icon" class="h-4" />
            <div class="text-base" :class="{ 'line-through': step.completed }">
              {{ step.title }}
            </div>
          </div>
        </component>
        <Button
          v-if="!step.completed && !isDependent(step)"
          :label="__('Skip')"
          class="!h-4 text-xs !text-ink-gray-6 hidden group-hover:flex"
          @click="() => skip(step.name, afterSkip)"
        />
        <Button
          v-else-if="!isDependent(step)"
          :label="__('Reset')"
          class="!h-4 text-xs !text-ink-gray-6 hidden group-hover:flex"
          @click.stop="() => reset(step.name, afterReset)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Badge, Button, Tooltip } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'

const props = defineProps({
  appName: {
    type: String,
    default: 'frappecrm',
  },
  title: {
    type: String,
    default: 'Frappe CRM',
  },
  logo: {
    type: Object,
    required: true,
  },
  afterSkip: {
    type: Function,
    default: () => {},
  },
  afterSkipAll: {
    type: Function,
    default: () => {},
  },
  afterReset: {
    type: Function,
    default: () => {},
  },
  afterResetAll: {
    type: Function,
    default: () => {},
  },
})

function isDependent(step) {
  if (step.dependsOn && !step.completed) {
    const dependsOnStep = steps.find((candidate) => {
      return candidate.name === step.dependsOn
    })
    if (dependsOnStep && !dependsOnStep.completed) {
      return true
    }
  }
  return false
}

function dependsOnTooltip(step) {
  if (step.dependsOn && !step.completed) {
    const dependsOnStep = steps.find((candidate) => {
      return candidate.name === step.dependsOn
    })
    if (dependsOnStep && !dependsOnStep.completed) {
      return __('You need to complete "{0}" first.', [dependsOnStep.title])
    }
  }
  return ''
}

const {
  steps,
  stepsCompleted,
  totalSteps,
  completedPercentage,
  skip,
  skipAll,
  reset,
  resetAll,
} = useOnboarding(props.appName)
</script>
