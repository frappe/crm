<template>
  <div
    :class="[
      'relative overflow-hidden rounded-lg border-2 transition-colors',
      disabled
        ? 'border-gray-200 bg-gray-50 opacity-50 dark:border-gray-700 dark:bg-gray-800'
        : isActive
          ? 'border-[color:var(--brand-primary,#bc1823)] bg-white'
          : 'border-gray-200 bg-white dark:border-gray-700',
    ]"
    :style="disabled ? 'pointer-events: none; user-select: none' : ''"
  >
    <canvas
      ref="canvasEl"
      class="block w-full touch-none"
      style="height: 180px"
      @mousedown="startDraw"
      @mousemove="draw"
      @mouseup="stopDraw"
      @mouseleave="stopDraw"
      @touchstart.prevent="startDrawTouch"
      @touchmove.prevent="drawTouch"
      @touchend="stopDraw"
    />

    <!-- Watermark — hidden once a stroke is drawn -->
    <div
      v-if="!hasStrokes"
      class="pointer-events-none absolute inset-0 flex items-center justify-center select-none text-sm text-gray-300 dark:text-gray-600"
    >
      Draw your signature here
    </div>

    <!-- Clear button -->
    <button
      v-if="hasStrokes && !disabled"
      type="button"
      class="absolute right-2 top-2 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-500 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
      @click="clearCanvas"
    >
      Clear
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['has-signature'])

const canvasEl = ref(null)
const hasStrokes = ref(false)
const isActive = ref(false)
let isDrawing = false
let ctx = null
let dpr = 1

let resizeObserver = null

onMounted(() => {
  initCanvas()
  // SF-3: reinit on viewport resize/orientation change so pointer coords stay aligned
  resizeObserver = new ResizeObserver(() => {
    initCanvas()
    hasStrokes.value = false
    emit('has-signature', false)
  })
  if (canvasEl.value) resizeObserver.observe(canvasEl.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

// Reinitialise when disabled switches to false (canvas may be zero-sized before reveal).
// IMPORTANT: initCanvas clears the bitmap — reset signature state to match.
watch(() => props.disabled, (val) => {
  if (!val) {
    setTimeout(() => {
      initCanvas()
      // Canvas was cleared by initCanvas; reflect that in state so a blank PNG is never submitted
      hasStrokes.value = false
      emit('has-signature', false)
    }, 0)
  }
})

function initCanvas() {
  const el = canvasEl.value
  if (!el) return
  dpr = window.devicePixelRatio || 1
  const rect = el.getBoundingClientRect()
  el.width = rect.width * dpr
  el.height = 180 * dpr
  ctx = el.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.strokeStyle = '#111111'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
}

// ---------------------------------------------------------------------------
// Mouse events
// ---------------------------------------------------------------------------

function getPos(event) {
  const rect = canvasEl.value.getBoundingClientRect()
  return { x: event.clientX - rect.left, y: event.clientY - rect.top }
}

function startDraw(event) {
  if (props.disabled) return
  isDrawing = true
  isActive.value = true
  const { x, y } = getPos(event)
  ctx.beginPath()
  ctx.moveTo(x, y)
}

function draw(event) {
  if (!isDrawing || props.disabled) return
  const { x, y } = getPos(event)
  ctx.lineTo(x, y)
  ctx.stroke()
  if (!hasStrokes.value) {
    hasStrokes.value = true
    emit('has-signature', true)
  }
}

function stopDraw() {
  isDrawing = false
  isActive.value = false
}

// ---------------------------------------------------------------------------
// Touch events
// ---------------------------------------------------------------------------

function getTouchPos(event) {
  const rect = canvasEl.value.getBoundingClientRect()
  const touch = event.touches[0]
  return { x: touch.clientX - rect.left, y: touch.clientY - rect.top }
}

function startDrawTouch(event) {
  if (props.disabled) return
  isDrawing = true
  isActive.value = true
  const { x, y } = getTouchPos(event)
  ctx.beginPath()
  ctx.moveTo(x, y)
}

function drawTouch(event) {
  if (!isDrawing || props.disabled) return
  const { x, y } = getTouchPos(event)
  ctx.lineTo(x, y)
  ctx.stroke()
  if (!hasStrokes.value) {
    hasStrokes.value = true
    emit('has-signature', true)
  }
}

// ---------------------------------------------------------------------------
// Clear
// ---------------------------------------------------------------------------

function clearCanvas() {
  const el = canvasEl.value
  if (!el || !ctx) return
  ctx.clearRect(0, 0, el.width / dpr, el.height / dpr)
  hasStrokes.value = false
  emit('has-signature', false)
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

function getSignatureDataUrl() {
  return canvasEl.value ? canvasEl.value.toDataURL('image/png') : ''
}

defineExpose({ getSignatureDataUrl, clearCanvas })
</script>
