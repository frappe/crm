<template>
  <TextInput
    ref="inputRef"
    :value="displayValue"
    v-bind="attrs"
    :placeholder="placeholder"
    @focus="handleFocus"
    @blur="handleBlur"
    @input="handleInput"
    @keydown="handleKeydown"
  />
  <p
    v-if="errorMessage || attrs.description"
    class="mt-1.5"
    :class="[sizeClass, errorMessage ? 'text-ink-red-3' : 'text-ink-gray-5']"
  >
    {{ errorMessage || attrs.description }}
  </p>
</template>

<script setup>
import { formatDuration } from '@/utils'
import { TextInput } from 'frappe-ui'
import { ref, computed, nextTick, useAttrs } from 'vue'

const props = defineProps({
  value: { type: Number, default: null },
  placeholder: { type: String, default: '1h 30m 45s' },
  longForm: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])

const attrs = useAttrs()
const inputRef = ref(null)
const isFocused = ref(false)
const editValue = ref('')
const errorMessage = ref('')
const isCommitting = ref(false)

const sizeClass = computed(() => {
  return { sm: 'text-xs', md: 'text-base' }[attrs.size || 'sm']
})

const displayValue = computed(() => {
  if (isFocused.value) return editValue.value
  return formatDuration(props.value, props.longForm)
})

function handleFocus() {
  isFocused.value = true
  editValue.value = formatDuration(props.value, props.longForm) || ''
  errorMessage.value = ''
  nextTick(() => {
    inputRef.value?.el?.select()
  })
}

function handleInput(e) {
  editValue.value = e.target.value
  errorMessage.value = ''
}

function handleBlur() {
  if (isCommitting.value) return
  commit()
}

function handleKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    isCommitting.value = true
    commit()
    inputRef.value?.el?.blur()
    isCommitting.value = false
  } else if (e.key === 'Escape') {
    revert()
    inputRef.value?.el?.blur()
  }
}

function commit() {
  const raw = editValue.value.trim()
  if (raw === '') {
    // Allow clearing the field
    errorMessage.value = ''
    isFocused.value = false
    emit('change', null)
    return
  }
  const seconds = parseDuration(raw)
  if (seconds === null) {
    errorMessage.value = props.longForm
      ? __(
          'Invalid format. Try: 1 hour 30 minutes, 2 hours, 45 seconds, 1:30:45, 90s',
        )
      : __('Invalid format. Try: 1h 30m 45s, 1:30:45, 90s')
    isFocused.value = false
  } else {
    errorMessage.value = ''
    isFocused.value = false
    emit('change', seconds)
  }
}

function revert() {
  errorMessage.value = ''
  isFocused.value = false
}

// ---------------------------------------------------------------------------
// Parse: human-readable string → seconds (integer) or null if invalid
//
// Supported formats (case-insensitive, spaces optional, any unit order):
//   1h 30m 45s | 4m 3h 4s | 4sec 3hour 4min | 1h30m45s
//   1:30:45    | 1:30     | :45
//   90         | 90s      (bare integer treated as seconds)
// ---------------------------------------------------------------------------
function parseDuration(str) {
  const input = str.trim().toLowerCase()
  if (!input) return null

  // Colon-separated: h:m:s or m:s or :s
  const colonRegex = /^(\d+):(\d+):(\d+)$|^(\d+):(\d+)$|^:(\d+)$/
  const colonMatch = input.match(colonRegex)
  if (colonMatch) {
    if (colonMatch[1] !== undefined) {
      return (
        parseInt(colonMatch[1], 10) * 3600 +
        parseInt(colonMatch[2], 10) * 60 +
        parseInt(colonMatch[3], 10)
      )
    } else if (colonMatch[4] !== undefined) {
      return parseInt(colonMatch[4], 10) * 60 + parseInt(colonMatch[5], 10)
    } else {
      return parseInt(colonMatch[6], 10)
    }
  }

  // Bare integer: treated as seconds
  if (/^\d+$/.test(input)) return parseInt(input, 10)

  // Named units in any order: scan (number)(unit) tokens left-to-right.
  // Verify no unexpected text exists between tokens.
  const tokenRe = /(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)/g
  const tokens = []
  let lastEnd = 0
  let match

  while ((match = tokenRe.exec(input)) !== null) {
    if (input.slice(lastEnd, match.index).trim() !== '') return null
    tokens.push({ value: parseInt(match[1], 10), unit: match[2][0] })
    lastEnd = match.index + match[0].length
  }

  if (input.slice(lastEnd).trim() !== '') return null
  if (tokens.length === 0) return null

  // Reject duplicate units (e.g. "1h 2h")
  const seen = new Set()
  for (const t of tokens) {
    if (seen.has(t.unit)) return null
    seen.add(t.unit)
  }

  let total = 0
  for (const { value, unit } of tokens) {
    if (unit === 'h') total += value * 3600
    else if (unit === 'm') total += value * 60
    else total += value
  }
  return total
}
</script>
