<template>
  <span
    data-slot="step-indicator"
    :data-state="state"
    :data-loading="running || undefined"
    class="relative inline-flex shrink-0 items-center justify-center"
    :class="[sizeClass, colorClass]"
  >
    <template v-if="running">
      <span
        class="lucide-circle absolute inset-0 size-full text-ink-gray-3"
        aria-hidden="true"
      />
      <span
        class="fui-step-arc lucide-circle absolute inset-0 size-full"
        aria-hidden="true"
      />
    </template>
    <span
      v-else
      class="absolute inset-0 size-full"
      :class="icon"
      aria-hidden="true"
    />
    <span
      v-if="number != null"
      class="relative text-2xs font-medium tabular-nums leading-none"
      :class="state === 'upcoming' ? 'text-ink-gray-5' : 'text-ink-gray-9'"
      aria-hidden="true"
    >
      {{ number }}
    </span>
    <span class="sr-only">{{ stateLabel }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StepState } from './types'

const props = defineProps<{
  state: StepState
  /** Indicator diameter: 20, 16 or 14px. */
  size: 'md' | 'sm' | 'xs'
  /** The current step is running. */
  loading?: boolean
  /** Top-level steps only; shown while the step is not finished. */
  index?: number
}>()

// Literal class strings so Tailwind's scanner picks every icon up.
const ICONS: Record<StepState, string> = {
  upcoming: 'lucide-circle',
  current: 'lucide-circle',
  complete: 'lucide-circle-check',
  failed: 'lucide-circle-alert',
  skipped: 'lucide-circle-minus',
}

const COLORS: Record<StepState, string> = {
  upcoming: 'text-ink-gray-4',
  current: 'text-ink-gray-9',
  complete: 'text-ink-gray-8',
  failed: 'text-ink-red-7',
  skipped: 'text-ink-gray-4',
}

const LABELS: Record<StepState, string> = {
  upcoming: 'not started',
  current: 'current',
  complete: 'completed',
  failed: 'failed',
  skipped: 'skipped',
}

const running = computed(() => props.state === 'current' && props.loading)
const unfinished = computed(
  () => props.state === 'current' || props.state === 'upcoming',
)
const number = computed(() =>
  props.index != null && unfinished.value ? props.index + 1 : null,
)

// A current sub-step (no number) marks itself with a dot instead.
const icon = computed(() =>
  props.state === 'current' && number.value == null
    ? 'lucide-circle-dot'
    : ICONS[props.state],
)
const colorClass = computed(() => COLORS[props.state])
const stateLabel = computed(() =>
  running.value ? 'running' : LABELS[props.state],
)
const sizeClass = computed(
  () => ({ md: 'size-5', sm: 'size-4', xs: 'size-3.5' })[props.size],
)
</script>

<style scoped>
/* Registered so the angle interpolates. The icon itself never rotates — only
   the paint inside its mask does, the same technique Spinner uses, so the
   circle cannot wobble on fractional pixels. */
@property --fui-step-arc-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

.fui-step-arc {
  background: conic-gradient(
    from var(--fui-step-arc-angle),
    transparent 0 45%,
    var(--ink-gray-8) 100%
  );
  animation: fui-step-arc 1.6s linear infinite;
}

@keyframes fui-step-arc {
  to {
    --fui-step-arc-angle: 360deg;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fui-step-arc {
    animation: none;
  }
}
</style>
