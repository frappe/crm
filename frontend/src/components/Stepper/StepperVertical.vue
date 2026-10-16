<template>
  <ol class="flex flex-col" :data-edge="edge">
    <li
      v-for="(step, i) in steps"
      :key="step.item.value"
      data-slot="step"
      :data-state="step.state"
      :aria-current="isCurrent(step) ? 'step' : undefined"
    >
      <!-- Only phrasing content inside, so the row is valid as a <button>. -->
      <component
        :is="isButton(step) ? 'button' : 'div'"
        :type="isButton(step) ? 'button' : undefined"
        class="flex items-stretch text-start"
        :class="[rowDirection, headClass(step)]"
        @click="isButton(step) && emit('select', step.item.value)"
      >
        <span
          class="flex min-w-0 flex-1 flex-col justify-center"
          :class="[textAlign, ui.headPad]"
        >
          <slot name="step-label" v-bind="slotProps(step)">
            <span
              class="break-words transition-colors group-hover:text-ink-gray-9 motion-reduce:transition-none"
              :class="[ui.title, TITLE[step.state]]"
              >{{ step.item.label }}</span
            >
          </slot>
          <slot name="step-description" v-bind="slotProps(step)">
            <span
              v-if="step.item.description"
              class="mt-px text-sm transition-colors group-hover:text-ink-gray-6 motion-reduce:transition-none"
              :class="CAPTION[step.state]"
            >
              {{ step.item.description }}
            </span>
          </slot>
        </span>
        <span
          v-if="step.item.meta || $slots['step-suffix']"
          class="order-first self-center text-sm tabular-nums text-ink-gray-5"
          :class="metaGap"
        >
          <slot name="step-suffix" v-bind="slotProps(step)">{{
            step.item.meta
          }}</slot>
        </span>
        <span
          class="flex shrink-0 flex-col items-center"
          :class="[ui.railWidth, railGap]"
        >
          <span
            class="fui-stepper-seg"
            :class="ui.segTop"
            v-bind="segAttrs(i, 'top')"
          />
          <slot name="step-prefix" v-bind="slotProps(step)">
            <StepIndicator
              :state="step.state"
              :size="ui.indicator"
              :loading="loading"
              :index="i"
            />
          </slot>
          <span
            class="fui-stepper-seg"
            :class="ui.segBottom"
            v-bind="segAttrs(i, 'bottom')"
          />
        </span>
      </component>

      <div
        v-if="showChildren(step)"
        class="flex items-stretch"
        :class="[rowDirection, bleed]"
      >
        <ol class="min-w-0 flex-1" :class="[textAlign, ui.subGap]">
          <li
            v-for="(child, j) in step.children"
            :key="child.item.value"
            data-slot="step"
            :data-state="child.state"
            :aria-current="isCurrent(child) ? 'step' : undefined"
            class="flex items-center gap-2.5"
            :class="rowDirection"
          >
            <span class="min-w-0 flex-1" :class="ui.subPad">
              <slot name="step-label" v-bind="slotProps(child)">
                <span
                  class="break-words"
                  :class="[ui.sub, SUB_TITLE[child.state]]"
                  >{{ child.item.label }}</span
                >
              </slot>
            </span>
            <span
              class="flex shrink-0 flex-col items-center self-stretch"
              :class="ui.subRailWidth"
            >
              <span
                class="fui-stepper-seg mb-px"
                v-bind="subSegAttrs(step, j, 'top')"
              />
              <slot name="step-prefix" v-bind="slotProps(child)">
                <StepIndicator
                  :state="child.state"
                  :size="ui.subIndicator"
                  :loading="loading"
                />
              </slot>
              <span
                class="fui-stepper-seg mt-px"
                v-bind="subSegAttrs(step, j, 'bottom')"
              />
            </span>
          </li>
        </ol>
        <div
          class="flex shrink-0 flex-col items-center"
          :class="[ui.railWidth, railGap]"
        >
          <span class="fui-stepper-seg" v-bind="segAttrs(i, 'through')" />
        </div>
      </div>
    </li>
  </ol>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import StepIndicator from './StepIndicator.vue'
import { isPassed } from './resolve'
import type {
  ResolvedStep,
  StepState,
  StepValue,
  StepperEdge,
  StepperSize,
} from './types'

const props = defineProps<{
  steps: ResolvedStep[]
  edge: StepperEdge
  size: StepperSize
  loading: boolean
  clickable: boolean
  substeps: 'all' | 'current'
}>()

const emit = defineEmits<{ select: [value: StepValue] }>()

const TITLE: Record<StepState, string> = {
  complete: 'text-ink-gray-7',
  current: 'text-ink-gray-9',
  failed: 'text-ink-gray-9',
  upcoming: 'text-ink-gray-5',
  skipped: 'text-ink-gray-5',
}
const SUB_TITLE: Record<StepState, string> = {
  complete: 'text-ink-gray-6',
  current: 'text-ink-gray-9',
  failed: 'text-ink-gray-9',
  upcoming: 'text-ink-gray-4',
  skipped: 'text-ink-gray-4',
}
const CAPTION: Record<StepState, string> = {
  complete: 'text-ink-gray-5',
  current: 'text-ink-gray-5',
  failed: 'text-ink-red-7',
  upcoming: 'text-ink-gray-4',
  skipped: 'text-ink-gray-4',
}

const SIZES = {
  md: {
    indicator: 'md',
    subIndicator: 'sm',
    title: 'text-base-medium',
    sub: 'text-base',
    headPad: 'py-3',
    subPad: 'py-1.5',
    subGap: 'pb-2.5',
    railWidth: 'w-5',
    subRailWidth: 'w-4',
    segTop: 'mb-0.5',
    segBottom: 'mt-0.5',
  },
  sm: {
    indicator: 'sm',
    subIndicator: 'xs',
    title: 'text-base',
    sub: 'text-sm',
    headPad: 'py-1.5',
    subPad: 'py-1',
    subGap: 'pb-0.5',
    railWidth: 'w-4',
    subRailWidth: 'w-3.5',
    segTop: 'mb-px',
    segBottom: 'mt-px',
  },
} as const

const ui = computed(() => SIZES[props.size])
// Label first in the DOM so it reads before the indicator's state word;
// `start` puts the indicator on the leading side visually.
const rowDirection = computed(() =>
  props.edge === 'start' ? 'flex-row-reverse' : 'flex-row',
)
const textAlign = computed(() =>
  props.edge === 'end' ? 'text-end' : 'text-start',
)
// Literal classes so Tailwind's scanner generates them.
const RAIL_GAP = {
  start: { md: 'me-3', sm: 'me-2.5' },
  end: { md: 'ms-3', sm: 'ms-2.5' },
} as const
const railGap = computed(() => RAIL_GAP[props.edge][props.size])
// Meta sits on the far side from the indicators: `order-first` lands it at the
// row's main start, which `flex-row-reverse` turns into the trailing edge.
const metaGap = computed(() => (props.edge === 'start' ? 'ms-2' : 'me-2'))
// With `clickable`, rows bleed 8px each side so the focus ring has room;
// every row does it, so the lines stay aligned.
const bleed = computed(() =>
  props.clickable ? '-mx-2 w-[calc(100%+1rem)] px-2' : '',
)

const isCurrent = (step: ResolvedStep) =>
  step.state === 'current' || step.state === 'failed'
const isButton = (step: ResolvedStep) => props.clickable && isPassed(step.state)
const slotProps = (step: ResolvedStep) => ({
  item: step.item,
  index: step.index,
  state: step.state,
})

function showChildren(step: ResolvedStep) {
  if (!step.children.length) return false
  return props.substeps === 'all' || isCurrent(step)
}

function headClass(step: ResolvedStep) {
  if (!isButton(step)) return bleed.value
  return [
    bleed.value,
    // Hover darkens the text (see the label and description), no fill.
    'group rounded-5 cursor-pointer focus-visible:focus-ring',
  ]
}

/** The line before step `i` fills once the step before it is passed. */
function segAttrs(i: number, part: 'top' | 'bottom' | 'through') {
  const last = i === props.steps.length - 1
  const hidden = part === 'top' ? i === 0 : last
  const owner = part === 'top' ? props.steps[i - 1] : props.steps[i]
  return {
    'data-hidden': hidden || undefined,
    'data-passed': (owner && isPassed(owner.state)) || undefined,
  }
}

function subSegAttrs(step: ResolvedStep, j: number, part: 'top' | 'bottom') {
  const hidden = part === 'top' ? j === 0 : j === step.children.length - 1
  const owner = part === 'top' ? step.children[j - 1] : step.children[j]
  return {
    'data-hidden': hidden || undefined,
    'data-passed': (owner && isPassed(owner.state)) || undefined,
  }
}
</script>

<style scoped>
.fui-stepper-seg {
  flex: 1 1 0;
  width: 1px;
  min-height: 0;
  background: var(--outline-gray-2);
  transition: background-color 300ms ease;
}
.fui-stepper-seg[data-passed] {
  background: var(--surface-gray-10);
}
.fui-stepper-seg[data-hidden] {
  visibility: hidden;
}
@media (prefers-reduced-motion: reduce) {
  .fui-stepper-seg {
    transition: none;
  }
}
</style>
