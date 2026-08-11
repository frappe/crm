<template>
  <div
    class="group fc-glass-card cursor-pointer"
    @click="$emit('click')"
  >
    <div class="flex flex-col gap-2">
      <div class="flex items-start justify-between gap-2">
        <span class="text-xs font-medium text-ink-gray-5 leading-tight">{{ label }}</span>
        <span
          class="w-7 h-7 flex-shrink-0 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105"
          :class="tone.chip"
          v-html="iconSvg"
        />
      </div>
      <div class="text-2xl font-bold text-ink-gray-9 tabular-nums truncate">
        {{ formattedValue }}
      </div>
      <div class="flex items-center gap-1 text-xs" v-if="deltaPct !== 0">
        <span :class="deltaClass" v-html="deltaIcon" />
        <span :class="deltaClass">{{ Math.abs(deltaPct) }}% vs last period</span>
      </div>
      <div v-else class="text-xs text-ink-gray-4">—</div>
    </div>
  </div>
</template>


<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  currency: { type: String, default: '' },
  deltaPct: { type: Number, default: 0 },
  deltaDirection: { type: String, default: 'neutral' },
  iconSvg: { type: String, default: '' },
  // Semantic tone: info | positive | attention | pending | neutral. Drives the
  // accent strip + icon chip through theme-aware frappe-ui tokens (auto dark).
  tone: { type: String, default: 'neutral' },
})
defineEmits(['click'])

// Restrained finance palette on a red/black/white brand (this fork rebrands the
// `blue` token family to Tiberbu red, so there is no blue tone). Each reads as a
// category: neutral (gray) balances · positive (green) cash in · attention (red)
// at-risk · pending (amber) awaiting. Chip = pale surface-*-2 fill + dark ink-*-6
// glyph (contrast-verified light & dark); rail = saturated surface-*-6.
const TONES = {
  neutral:   { chip: 'bg-surface-gray-3 text-ink-gray-7' },
  positive:  { chip: 'bg-surface-green-2 text-ink-green-6' },
  attention: { chip: 'bg-surface-red-2 text-ink-red-6' },
  pending:   { chip: 'bg-surface-amber-2 text-ink-amber-6' },
}
const tone = computed(() => TONES[props.tone] || TONES.neutral)

const deltaClass = computed(() =>
  props.deltaDirection === 'up'
    ? 'text-ink-green-6'
    : props.deltaDirection === 'down'
      ? 'text-ink-red-6'
      : 'text-ink-gray-4',
)

const formattedValue = computed(() => {
  const v = props.value ?? 0
  const prefix = props.currency ? props.currency + ' ' : ''
  if (v >= 1_000_000) return prefix + (v / 1_000_000).toFixed(1) + 'M'
  if (v >= 1_000)     return prefix + (v / 1_000).toFixed(0) + 'K'
  return prefix + v.toLocaleString(undefined, { maximumFractionDigits: 0 })
})

const deltaIcon = computed(() => {
  if (props.deltaDirection === 'up')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>'
  if (props.deltaDirection === 'down')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"/><path d="m19 12-7 7-7-7"/></svg>'
  return ''
})
</script>
