<template>
  <div
    class="flex gap-2 border border-outline-gray-2 rounded w-fit min-w-max px-4 select-none shadow-sm"
  >
    <div
      v-if="displayOptions.hours"
      class="p-2 flex flex-col items-center group relative"
    >
      <div class="flex items-center gap-1">
        <input
          ref="hoursInput"
          v-model.number="hoursValue"
          type="number"
          min="0"
          class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-ink-gray-8"
          @blur="validateAndUpdateTime('hours')"
          @keyup.enter="handleEnter"
        />
        <div
          class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
        >
          <button
            @mousedown="startAction(() => increment('hours'))"
            @touchstart="startAction(() => increment('hours'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-up" class="size-3.5" />
          </button>
          <button
            @mousedown="startAction(() => decrement('hours'))"
            @touchstart="startAction(() => decrement('hours'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-down" class="size-3.5" />
          </button>
        </div>
      </div>
      <div class="text-xs text-gray-600 mt-1">Hrs</div>
    </div>
    <div
      v-if="displayOptions.minutes"
      class="p-2 flex flex-col items-center group relative"
    >
      <div class="flex items-center gap-1">
        <input
          ref="minutesInput"
          v-model.number="minutesValue"
          type="number"
          min="0"
          max="59"
          class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-ink-gray-8"
          @blur="validateAndUpdateTime('minutes')"
          @keyup.enter="handleEnter"
        />
        <div
          class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
        >
          <button
            @mousedown="startAction(() => increment('minutes'))"
            @touchstart="startAction(() => increment('minutes'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-up" class="size-3.5" />
          </button>
          <button
            @mousedown="startAction(() => decrement('minutes'))"
            @touchstart="startAction(() => decrement('minutes'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-down" class="size-3.5" />
          </button>
        </div>
      </div>
      <div class="text-xs text-gray-600 mt-1">Min</div>
    </div>
    <div
      v-if="displayOptions.seconds"
      class="p-2 flex flex-col items-center group relative"
    >
      <div class="flex items-center gap-1">
        <input
          ref="secondsInput"
          v-model.number="secondsValue"
          type="number"
          min="0"
          max="59"
          class="w-8 text-sm bg-transparent border-0 p-0 text-center focus:ring-0 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          @blur="validateAndUpdateTime('seconds')"
          @keyup.enter="handleEnter"
        />
        <div
          class="flex flex-col group-hover:opacity-100 opacity-0 absolute top-1/2 -translate-y-1/2 -right-3"
        >
          <button
            @mousedown="startAction(() => increment('seconds'))"
            @touchstart="startAction(() => increment('seconds'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-up" class="size-3.5" />
          </button>
          <button
            @mousedown="startAction(() => decrement('seconds'))"
            @touchstart="startAction(() => decrement('seconds'))"
            @mouseup="clearActiveInterval"
            @mouseleave="clearActiveInterval"
            @touchend="clearActiveInterval"
            @touchcancel="clearActiveInterval"
            class="hover:bg-surface-gray-1 text-ink-gray-8 rounded-sm select-none"
          >
            <FeatherIcon name="chevron-down" class="size-3.5" />
          </button>
        </div>
      </div>
      <div class="text-xs text-gray-600 mt-1">Sec</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits, defineProps, onUnmounted } from 'vue'

const props = defineProps({
  min: { type: Number, default: 0 },
  max: { type: Number, default: Number.MAX_SAFE_INTEGER },
  options: { type: Object, default: () => ({}) },
})

const modelValue = defineModel({ default: 0 })

const normalizedOptions = computed(() => ({
  hours: props.options?.hours ?? true,
  minutes: props.options?.minutes ?? true,
  seconds: props.options?.seconds ?? false,
}))

const displayOptions = computed(() => {
  const { hours, minutes, seconds } = normalizedOptions.value
  if (!hours && !minutes && !seconds) {
    return { hours: true, minutes: true, seconds: false }
  }
  return { hours, minutes, seconds }
})

const emit = defineEmits(['change'])

const hoursInput = ref(null)
const minutesInput = ref(null)
const secondsInput = ref(null)
const activeInterval = ref(null)
const activeAction = ref(null)
const initialDelay = 300
const repeatDelay = 50
let isMouseDown = false
let actionTimeout = null

const hoursValue = computed({
  get: () => Math.floor(modelValue.value / 3600).toString(),
  set: (value) => {
    if (value === '') return
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 0) {
      const newTime = num * 3600 + getMinutes() * 60 + getSeconds()
      updateTime(newTime)
    }
  },
})

const minutesValue = computed({
  get: () => Math.floor((modelValue.value % 3600) / 60).toString(),
  set: (value) => {
    if (value === '') return
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 0 && num <= 59) {
      const newTime = getHours() * 3600 + num * 60 + getSeconds()
      updateTime(newTime)
    }
  },
})

const secondsValue = computed({
  get: () => (modelValue.value % 60).toString(),
  set: (value) => {
    if (value === '') return
    const num = parseInt(value, 10)
    if (!isNaN(num) && num >= 0 && num <= 59) {
      const newTime = getHours() * 3600 + getMinutes() * 60 + num
      updateTime(newTime)
    }
  },
})

function getHours() {
  return Math.floor(modelValue.value / 3600)
}

function getMinutes() {
  return Math.floor((modelValue.value % 3600) / 60)
}

function getSeconds() {
  return modelValue.value % 60
}

// Clear any active intervals when component unmounts
onUnmounted(() => {
  clearActiveInterval()
  if (actionTimeout) {
    clearTimeout(actionTimeout)
  }
})

function clearActiveInterval() {
  if (activeInterval.value !== null) {
    clearInterval(activeInterval.value)
    activeInterval.value = null
  }
  if (actionTimeout) {
    clearTimeout(actionTimeout)
    actionTimeout = null
  }
  isMouseDown = false
}

function startAction(action) {
  if (isMouseDown) return

  isMouseDown = true

  action()

  actionTimeout = setTimeout(() => {
    if (!isMouseDown) return

    activeAction.value = action
    activeInterval.value = setInterval(() => {
      if (activeAction.value) {
        activeAction.value()
      }
    }, repeatDelay)
  }, initialDelay)
}

function handlePointerUp() {
  clearActiveInterval()
}

document.addEventListener('mouseup', handlePointerUp)
document.addEventListener('touchend', handlePointerUp)
onUnmounted(() => {
  document.removeEventListener('mouseup', handlePointerUp)
  document.removeEventListener('touchend', handlePointerUp)
})

function updateTime(newTime, emitEvent = true) {
  newTime = Math.max(props.min, Math.min(props.max, newTime))
  if (newTime !== modelValue.value) {
    modelValue.value = newTime
    if (emitEvent) {
      emit('change', modelValue.value)
    }
  }
}

function validateAndUpdateTime(unit) {
  switch (unit) {
    case 'hours':
      hoursValue.value = hoursValue.value
      break
    case 'minutes':
      minutesValue.value = minutesValue.value
      break
    case 'seconds':
      secondsValue.value = secondsValue.value
      break
  }
}

function handleEnter(e) {
  e.target.blur()
}

function increment(unit) {
  let newTime = modelValue.value
  switch (unit) {
    case 'hours':
      newTime += 3600
      break
    case 'minutes':
      newTime += 60
      break
    case 'seconds':
      newTime += 1
      break
  }
  updateTime(newTime)
}

function decrement(unit) {
  let newTime = modelValue.value
  switch (unit) {
    case 'hours':
      newTime -= 3600
      break
    case 'minutes':
      newTime -= 60
      break
    case 'seconds':
      newTime -= 1
      break
  }
  updateTime(newTime)
}
</script>

<style scoped>
button {
  outline: none;
  -webkit-tap-highlight-color: transparent;
}
</style>
