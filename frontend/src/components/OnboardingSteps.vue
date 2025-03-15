<template>
  <div class="flex flex-col justify-center items-center gap-1 mt-4 mb-7">
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
      <Badge
        :label="__('{0}% completed', [completedPercentage])"
        theme="orange"
        size="lg"
      />
      <div class="flex">
        <Button
          v-if="completedPercentage != 0"
          variant="ghost"
          :label="__('Reset')"
          @click="reset"
        />
        <Button
          v-if="completedPercentage != 100"
          variant="ghost"
          :label="__('Skip all')"
          @click="skipAll"
        />
      </div>
    </div>
    <div class="flex flex-col gap-1.5 overflow-y-auto">
      <div
        v-for="step in steps"
        :key="step.title"
        class="group w-full flex gap-2 justify-between items-center hover:bg-surface-gray-1 rounded px-2 py-1.5 cursor-pointer"
        @click.stop="() => !step.completed && step.onClick()"
      >
        <div
          class="flex gap-2 items-center"
          :class="[step.completed ? 'text-ink-gray-5' : 'text-ink-gray-8']"
        >
          <component :is="step.icon" class="h-4" />
          <div class="text-base" :class="{ 'line-through': step.completed }">
            {{ step.title }}
          </div>
        </div>
        <Button
          v-if="!step.completed"
          :label="__('Skip')"
          class="!h-4 text-xs !text-ink-gray-6 hidden group-hover:flex"
          @click="() => skip(step.name)"
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { useOnboarding } from '@/composables/onboarding'

const emit = defineEmits(['close'])

const {
  steps,
  stepsCompleted,
  totalSteps,
  completedPercentage,
  skip,
  skipAll,
  reset,
} = useOnboarding()
</script>
