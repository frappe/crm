<template>
  <div>
    <!-- The stock Progress, used as it ships: one interval per step. -->
    <Progress :value="value" :intervals="steps.length" />
    <ol class="mt-2.5 grid auto-cols-fr grid-flow-col gap-x-1">
      <li
        v-for="(step, i) in steps"
        :key="step.item.value"
        data-slot="step"
        :data-state="step.state"
        :aria-current="isCurrent(step) ? 'step' : undefined"
        class="min-w-0"
      >
        <NativeTag
          :as="isButton(step) ? 'button' : 'div'"
          :type="isButton(step) ? 'button' : undefined"
          class="flex w-full min-w-0 items-center gap-1.5 text-start"
          :class="isButton(step) && BUTTON"
          @click="isButton(step) && emit('select', step.item.value)"
        >
          <slot name="step-prefix" v-bind="slotProps(step)">
            <StepIndicator
              :state="step.state"
              :size="indicator"
              :loading="loading"
              :index="i"
            />
          </slot>
          <slot name="step-label" v-bind="slotProps(step)">
            <span
              class="truncate transition-colors group-hover:text-ink-gray-9 motion-reduce:transition-none"
              :class="[title, TITLE[step.state]]"
              :title="step.item.label"
            >
              {{ step.item.label }}
            </span>
          </slot>
        </NativeTag>
      </li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Progress } from 'frappe-ui'
import NativeTag from './NativeTag'
import StepIndicator from './StepIndicator.vue'
import { isPassed } from './resolve'
import type { ResolvedStep, StepState, StepValue, StepperSize } from './types'

const props = defineProps<{
  steps: ResolvedStep[]
  size: StepperSize
  loading: boolean
  clickable: boolean
}>()

const emit = defineEmits<{ select: [value: StepValue] }>()

const TITLE: Record<StepState, string> = {
  complete: 'text-ink-gray-7',
  current: 'text-ink-gray-9',
  failed: 'text-ink-gray-9',
  upcoming: 'text-ink-gray-5',
  skipped: 'text-ink-gray-5',
}

const BUTTON = [
  // Hover darkens the label, no fill; the inset gives the focus ring room.
  'group -mx-1 w-[calc(100%+0.5rem)] px-1 rounded-4 cursor-pointer',
  'focus-visible:focus-ring',
]

const indicator = computed(() => (props.size === 'sm' ? 'xs' : 'sm'))
const title = computed(() =>
  props.size === 'sm' ? 'text-sm' : 'text-sm-medium',
)

/** An interval fills once its step is done or skipped. */
const value = computed(() => {
  const passed = props.steps.filter((s) => isPassed(s.state)).length
  return props.steps.length ? (passed / props.steps.length) * 100 : 0
})

const isCurrent = (step: ResolvedStep) =>
  step.state === 'current' || step.state === 'failed'
const isButton = (step: ResolvedStep) =>
  props.clickable && (isPassed(step.state) || step.item.selectable === true)
const slotProps = (step: ResolvedStep) => ({
  item: step.item,
  index: step.index,
  state: step.state,
})
</script>
