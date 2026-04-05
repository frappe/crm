<template>
  <Tooltip :text="tooltipText" placement="right" :hoverDelay="0">
    <div
      class="rating-stars inline-flex flex-wrap items-center gap-0.5 transition-opacity"
      :class="disabled ? 'opacity-50' : ''"
      v-bind="$attrs"
      @mouseleave="onMouseLeave"
    >
      <button
        v-for="i in nStars"
        :key="i"
        type="button"
        class="focus:outline-none leading-none rating-star"
        :class="disabled ? 'cursor-default' : 'cursor-pointer'"
        @mousemove="!disabled && onMouseMove($event, i)"
        @click="!disabled && onStarClick($event, i)"
      >
        <!--
          Three visual states during hover:
            FILLED  (yellow-500) — committed stars that are staying
            PREVIEW (yellow-200) — stars that will be added on click
            REMOVING(yellow-300) — committed stars that will be removed on click
        -->
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
          <path
            d="M11.9987 3.00011C11.8207 3.00011 11.6428 3.09261 11.5509 3.27762L9.15562 8.09836C9.08253 8.24546 8.94185 8.34728 8.77927 8.37075L3.42887 9.14298C3.01771 9.20233 2.85405 9.70811 3.1525 9.99707L7.01978 13.7414C7.13858 13.8564 7.19283 14.0228 7.16469 14.1857L6.25116 19.4762C6.18071 19.8842 6.6083 20.1961 6.97531 20.0045L11.7672 17.5022C11.8397 17.4643 11.9192 17.4454 11.9987 17.4454V3.00011Z"
            :style="{
              fill: getHalfColor(i - 0.5),
              stroke: getHalfColor(i - 0.5),
            }"
          />
          <path
            d="M11.9987 3.00011C12.177 3.00011 12.3554 3.09303 12.4471 3.27888L14.8213 8.09112C14.8941 8.23872 15.0349 8.34102 15.1978 8.3647L20.5069 9.13641C20.917 9.19602 21.0807 9.69992 20.7841 9.9892L16.9421 13.7354C16.8243 13.8503 16.7706 14.0157 16.7984 14.1779L17.7053 19.4674C17.7753 19.8759 17.3466 20.1874 16.9798 19.9945L12.2314 17.4973C12.1586 17.459 12.0786 17.4398 11.9987 17.4398V3.00011Z"
            :style="{ fill: getHalfColor(i), stroke: getHalfColor(i) }"
          />
        </svg>
      </button>
    </div>
  </Tooltip>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Tooltip } from 'frappe-ui'

const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: [Number, String], default: 5 },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])

const nStars = computed(() => Number(props.max) || 5)
const hoveredStarValue = ref(null)

// Saved value in star-units, rounded to nearest 0.5
const savedStarValue = computed(() => {
  const raw = (props.value || 0) * nStars.value
  return Math.round(raw * 2) / 2
})

// CSS custom properties — values defined in <style> block, dark mode overridden there
const FILLED = 'var(--rating-filled)'
const PREVIEW = 'var(--rating-preview)'
const REMOVING = 'var(--rating-removing)'
const EMPTY = 'var(--rating-empty)'

/**
 * Each star is two half-values: (i - 0.5) for left, (i) for right.
 * During hover we show three states so the saved rating stays readable:
 *   halves ≤ min(saved, hovered) → FILLED   (committed & staying)
 *   halves >  saved, ≤ hovered  → PREVIEW   (will be added)
 *   halves >  hovered, ≤ saved  → REMOVING  (will be cleared)
 *   halves >  max(saved, hovered)→ EMPTY
 */
function getHalfColor(halfValue) {
  const saved = savedStarValue.value
  const hovered = hoveredStarValue.value

  if (hovered === null) {
    return halfValue <= saved ? FILLED : EMPTY
  }
  if (halfValue <= Math.min(saved, hovered)) return FILLED
  if (halfValue <= hovered) return PREVIEW
  if (halfValue <= saved) return REMOVING
  return EMPTY
}

// Tooltip text: in read-only mode shows saved value on hover;
// in interactive mode shows hovered preview value while hovering
const tooltipText = computed(() => {
  const display = props.disabled ? savedStarValue.value : hoveredStarValue.value
  if (!display) return null
  const label = display % 1 === 0 ? String(display) : display.toFixed(1)
  return `${label} / ${nStars.value}`
})

function onMouseMove(event, i) {
  const rect = event.currentTarget.getBoundingClientRect()
  hoveredStarValue.value =
    event.clientX - rect.left < rect.width / 2 ? i - 0.5 : i
}

function onMouseLeave() {
  hoveredStarValue.value = null
}

function onStarClick(event, i) {
  const rect = event.currentTarget.getBoundingClientRect()
  const isLeftHalf = event.clientX - rect.left < rect.width / 2
  let newStarValue = isLeftHalf ? i - 0.5 : i

  // Toggle off when clicking the already-set value
  const currentStarValue = Math.round((props.value || 0) * nStars.value * 2) / 2
  if (newStarValue === currentStarValue) newStarValue = 0

  emit('change', newStarValue / nStars.value)
}
</script>

<style scoped>
/* Light mode */
.rating-stars {
  --rating-filled: #eab308; /* yellow-500 */
  --rating-preview: #fde68a; /* yellow-200 */
  --rating-removing: #fcd34d; /* yellow-300 */
  --rating-empty: #d1d5db; /* gray-300   */
}

/* Dark mode — [data-theme="dark"] is how frappe-ui activates dark mode */
[data-theme='dark'] .rating-stars {
  --rating-filled: #eab308; /* yellow-500 — same, readable on dark */
  --rating-preview: #fde68a; /* yellow-200 — bright preview on dark  */
  --rating-removing: #fcd34d; /* yellow-300                           */
  --rating-empty: #4b5563; /* gray-600   — visible on dark bg      */
}
</style>
