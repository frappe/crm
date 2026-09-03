<template>
  <div class="space-y-2">
    <div class="flex items-start gap-2">
      <div class="flex w-5 shrink-0 justify-center pt-2.5">
        <Spinner v-if="state === 'running'" size="sm" class="text-ink-gray-7" />
        <component
          :is="STATUS_ICONS[state]"
          v-else-if="STATUS_ICONS[state]"
          class="size-4"
          :class="STATUS_COLORS[state]"
        />
        <span v-else class="mt-1.5 size-1.5 rounded-full bg-surface-gray-4" />
      </div>

      <div
        class="min-w-0 flex-1 rounded-[10px] border bg-surface-base px-3 py-2 shadow-sm transition-opacity"
        :class="[cardClasses, { 'opacity-50': dimmed }]"
      >
        <div class="flex items-center gap-2">
          <div
            class="flex size-[26px] shrink-0 items-center justify-center rounded-[6px] border border-outline-gray-2"
          >
            <component :is="presentation.icon" class="size-4 text-ink-gray-7" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-base-medium text-ink-gray-8">
              {{ presentation.label }}
            </div>
            <div
              v-if="presentation.detail"
              class="truncate text-xs text-ink-gray-5"
            >
              {{ presentation.detail }}
            </div>
          </div>
          <Badge
            v-if="forced"
            :label="__('Forced')"
            theme="orange"
            variant="subtle"
          />
          <span class="shrink-0 text-xs text-ink-gray-5">
            {{ presentation.kicker }}
          </span>
        </div>

        <div
          v-if="outcome"
          class="mt-1.5 space-y-1 border-t border-outline-gray-1 pt-1.5"
        >
          <div class="text-xs" :class="detailColor">
            {{ outcome.message || outcome.detail }}
          </div>
          <div v-if="outcome.condition" class="space-y-0.5">
            <code class="block break-words text-xs text-ink-gray-7">
              {{ outcome.condition }}
            </code>
            <div
              v-for="(value, name) in outcome.condition_values"
              :key="name"
              class="text-xs text-ink-gray-5"
            >
              {{ name }} = {{ JSON.stringify(value) }}
            </div>
          </div>
          <details v-if="outcome.traceback">
            <summary class="cursor-pointer text-xs text-ink-gray-5">
              {{ __('Technical details') }}
            </summary>
            <pre class="mt-1 overflow-x-auto text-xs text-ink-gray-6">{{
              outcome.traceback
            }}</pre>
          </details>
        </div>
      </div>
    </div>

    <div
      v-if="isBranching(node)"
      class="ml-5 space-y-3 border-l border-outline-gray-2 pl-4"
    >
      <div v-for="arm in arms" :key="arm.name" class="space-y-2">
        <div class="flex items-center gap-2">
          <span
            class="text-xs-semibold"
            :class="arm.taken ? 'text-ink-gray-7' : 'text-ink-gray-4'"
          >
            {{ arm.label }}
          </span>
          <Button
            v-if="canRunArm(arm)"
            variant="ghost"
            size="sm"
            :label="__('Run this branch')"
            @click="$emit('run-branch', { idx: branchIdx, arm: arm.name })"
          />
        </div>
        <div v-if="!arm.steps.length" class="text-xs text-ink-gray-5">
          {{ __('Nothing here') }}
        </div>
        <WorkflowTrialStep
          v-for="child in arm.steps"
          :key="child._id"
          v-bind="{
            ...$props,
            node: child,
            offPath: dimmed || arm.taken === false,
          }"
          @run-branch="$emit('run-branch', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import FailedIcon from '~icons/lucide/circle-x'
import SkippedIcon from '~icons/lucide/circle-minus'
import SuccessIcon from '~icons/lucide/circle-check'
import WaitingIcon from '~icons/lucide/clock'
import { stepPresentation } from './workflowGraph'
import { armLabels, isBranching } from './workflowSteps'
import { Badge, Button, Spinner } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  outcomes: { type: Object, required: true },
  activeKey: { type: String, default: '' },
  taken: { type: Object, required: true },
  overrides: { type: Object, required: true },
  rowIdx: { type: Object, required: true },
  playing: { type: Boolean, default: false },
  finished: { type: Boolean, default: false },
  // An arm the run did not take: its steps are drawn, but never ran.
  offPath: { type: Boolean, default: false },
})

defineEmits(['run-branch'])

const STATUS_ICONS = {
  Success: SuccessIcon,
  Skipped: SkippedIcon,
  Failed: FailedIcon,
  Waiting: WaitingIcon,
}

const STATUS_COLORS = {
  Success: 'text-ink-green-5',
  Skipped: 'text-ink-gray-4',
  Failed: 'text-ink-red-5',
  Waiting: 'text-ink-amber-6',
}

const presentation = computed(() => stepPresentation(props.node))

const outcome = computed(() => props.outcomes[props.node.step_key] || null)

const state = computed(() => {
  if (props.activeKey === props.node.step_key) return 'running'
  return outcome.value?.status || ''
})

// Only a finished run can say a step did not run; before that every block reads as ready.
const dimmed = computed(
  () => props.offPath || (props.finished && !outcome.value),
)

/** The `If` row that decides this step's arms - for a wait, the outcome row folded into it. */
const branchIdx = computed(() => {
  const key = props.node._outcomeKey || props.node.step_key
  return props.rowIdx[key]
})

const forced = computed(() => Boolean(props.overrides[String(branchIdx.value)]))

const arms = computed(() => {
  const labels = armLabels(props.node)
  const chosen = props.taken[String(branchIdx.value)]
  return ['If', 'Else'].map((name) => ({
    name,
    label: labels[name],
    steps: props.node.children?.[name] || [],
    taken: chosen ? chosen === name : null,
  }))
})

const detailColor = computed(() => {
  if (outcome.value?.status === 'Failed') return 'text-ink-red-5'
  return 'text-ink-gray-6'
})

const cardClasses = computed(() => {
  if (state.value === 'Failed') return 'border-outline-red-2'
  if (state.value === 'running') return 'border-outline-gray-4'
  return 'border-outline-gray-2'
})

/** Offered on the arm this record did not reach, so the other path can still be tried. */
function canRunArm(arm) {
  return arm.taken === false && arm.steps.length && !props.playing
}
</script>
