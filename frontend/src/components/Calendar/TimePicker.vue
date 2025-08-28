<template>
  <Popover
    v-model:show="showOptions"
    transition="default"
    :placement="placement"
    @update:show="
      (v) => {
        if (!v) emit('close')
      }
    "
  >
    <template #target="{ togglePopover, isOpen }">
      <TextInput
        ref="inputRef"
        v-model="displayValue"
        :variant="variant"
        type="text"
        class="text-sm w-full cursor-text"
        :placeholder="placeholder"
        :disabled="disabled"
        @focus="onFocus(isOpen, togglePopover)"
        @click="onClickInput(isOpen, togglePopover)"
        @keydown.enter.prevent="onEnter"
        @blur="commitInput"
        @keydown.down.prevent="onArrowDown(togglePopover, isOpen)"
        @keydown.up.prevent="onArrowUp(togglePopover, isOpen)"
        @keydown.esc.prevent="onEscape"
      >
        <template #suffix>
          <slot name="suffix" v-bind="{ togglePopover, isOpen }">
            <FeatherIcon
              name="chevron-down"
              class="h-4 w-4 cursor-pointer"
              @mousedown.prevent="togglePopover"
            />
          </slot>
        </template>
      </TextInput>
    </template>
    <template #body="{ isOpen }">
      <div
        v-show="isOpen"
        ref="panelRef"
        class="mt-2 max-h-48 w-44 overflow-y-auto rounded-lg bg-surface-modal p-1 text-base shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
        role="listbox"
        :aria-activedescendant="activeDescendantId"
      >
        <button
          v-for="(opt, idx) in displayedOptions"
          :key="opt.value"
          :data-value="opt.value"
          :data-index="idx"
          type="button"
          class="group flex h-7 w-full items-center rounded px-2 text-left"
          :class="buttonClasses(opt, idx)"
          @click="() => select(opt.value, autoClose)"
          @mouseenter="highlightIndex = idx"
          role="option"
          :id="optionId(idx)"
          :aria-selected="internalValue === opt.value"
        >
          <span class="truncate">{{ opt.label }}</span>
        </button>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Popover, TextInput } from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' }, // Expect 24h format HH:MM (seconds in HH:MM:SS accepted & truncated), parses flexible input
  interval: { type: Number, default: 15 },
  options: {
    // Optional complete override of generated options (array of { value: 'HH:MM', label?: string })
    type: Array,
    default: () => [],
  },
  placement: { type: String, default: 'bottom-start' },
  placeholder: { type: String, default: 'Select time' },
  variant: { type: String, default: 'outline' },
  allowCustom: { type: Boolean, default: true },
  autoClose: { type: Boolean, default: true },
  use12Hour: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  scrollMode: { type: String, default: 'center' }, // center | start | nearest
  amLabel: { type: String, default: 'am' },
  pmLabel: { type: String, default: 'pm' },
  minTime: { type: String, default: '' }, // inclusive HH:MM 24h
  maxTime: { type: String, default: '' }, // inclusive HH:MM 24h
})
const emit = defineEmits([
  'update:modelValue',
  'input-invalid',
  'invalid-change',
  'open',
  'close',
])

const panelRef = ref(null)
const showOptions = ref(false)
const highlightIndex = ref(-1)
const hasSelectedOnFirstClick = ref(false)
const isTyping = ref(false)
let navUpdating = false
let invalidState = false
const inputRef = ref(null)
const internalValue = ref(props.modelValue) // always normalized 24h HH:MM or ''
const displayValue = ref(formatDisplay(internalValue.value))
const uid = Math.random().toString(36).slice(2, 9)
const activeDescendantId = computed(() =>
  highlightIndex.value > -1 ? optionId(highlightIndex.value) : null,
)
function optionId(idx) {
  return `tp-${uid}-${idx}`
}

function minutesFromHHMM(str) {
  if (!str) return null
  if (!/^\d{2}:\d{2}(:\d{2})?$/.test(str)) return null
  const [h, m] = str.split(':').map((n) => parseInt(n))
  if (h > 23 || m > 59) return null
  return h * 60 + m // ignore seconds if provided
}
const minMinutes = computed(() => minutesFromHHMM(props.minTime))
const maxMinutes = computed(() => minutesFromHHMM(props.maxTime))

const displayedOptions = computed(() => {
  if (props.options?.length) {
    return props.options.map((o) => ({
      value: normalize24(o.value),
      label: o.label || formatDisplay(normalize24(o.value)),
    }))
  }
  const out = []
  for (let m = 0; m < 1440; m += props.interval) {
    if (minMinutes.value != null && m < minMinutes.value) continue
    if (maxMinutes.value != null && m > maxMinutes.value) continue
    const hh = Math.floor(m / 60)
      .toString()
      .padStart(2, '0')
    const mm = (m % 60).toString().padStart(2, '0')
    const val = `${hh}:${mm}`
    out.push({
      value: val,
      label: formatDisplay(val),
    })
  }
  return out
})

watch(
  () => props.modelValue,
  (nv) => {
    if (nv && nv !== internalValue.value) {
      internalValue.value = normalize24(nv)
      displayValue.value = formatDisplay(internalValue.value)
    } else if (!nv) {
      internalValue.value = ''
      displayValue.value = ''
    }
  },
)

function normalize24(raw) {
  if (!raw) return ''
  // already HH:MM 24h
  if (/^\d{2}:\d{2}$/.test(raw)) return raw
  // HH:MM:SS -> truncate seconds
  if (/^\d{2}:\d{2}:\d{2}$/.test(raw)) return raw.slice(0, 5)
  const parsed = parseFlexibleTime(raw)
  return parsed.valid ? parsed.hh24 + ':' + parsed.mm : ''
}

function formatDisplay(val24) {
  if (!val24) return ''
  const [h, m] = val24.split(':').map((n) => parseInt(n))
  if (!props.use12Hour)
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
  const am = h < 12
  const hour12 = h % 12 === 0 ? 12 : h % 12
  return `${hour12}:${m.toString().padStart(2, '0')} ${am ? props.amLabel : props.pmLabel}`
}

function parseFlexibleTime(input) {
  if (!input) return { valid: false }
  let s = input.trim().toLowerCase()
  s = s.replace(/\./g, '') // remove periods like a.m.
  // Insert space before am/pm if missing
  s = s.replace(/(\d)(am|pm)$/, '$1 $2')
  // supports: H, HH, HMM, HHMM, H:MM, HH:MM, HH:MM:SS, H:MM:SS + optional am/pm
  // Simplify by using explicit colon format: H{1,2}(:MM)?(:SS)? with constraint that if SS present, MM must be present
  const re = /^(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?\s*([ap]m)?$/
  const m = s.match(re)
  if (!m) return { valid: false }
  let [, hhStr, mmStr, ssStr, ap] = m
  let hh = parseInt(hhStr)
  if (isNaN(hh) || hh < 0 || hh > 23) return { valid: false }
  // If seconds provided but minutes missing -> invalid
  if (ssStr && !mmStr) return { valid: false }
  let mm = mmStr != null && mmStr !== '' ? parseInt(mmStr) : 0
  if (isNaN(mm) || mm < 0 || mm > 59) return { valid: false }
  if (ssStr) {
    const ss = parseInt(ssStr)
    if (isNaN(ss) || ss < 0 || ss > 59) return { valid: false }
    // seconds currently ignored for internal value & total
  }
  if (ap) {
    if (hh === 12 && ap === 'am') hh = 0
    else if (hh < 12 && ap === 'pm') hh += 12
  }
  return {
    valid: true,
    hh24: hh.toString().padStart(2, '0'),
    mm: mm.toString().padStart(2, '0'),
    total: hh * 60 + mm,
  }
}

// Returns index of nearest value (by minutes) using binary search on sorted list
function findNearestIndex(targetMinutes, list) {
  if (!list.length) return -1
  const minutesArr = list.map((o) => {
    const [hh, mm] = o.value.split(':').map(Number)
    return hh * 60 + mm
  })
  let lo = 0,
    hi = minutesArr.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const val = minutesArr[mid]
    if (val === targetMinutes) return mid
    if (val < targetMinutes) lo = mid + 1
    else hi = mid - 1
  }
  const candidates = []
  if (lo < minutesArr.length) candidates.push(lo)
  if (lo - 1 >= 0) candidates.push(lo - 1)
  if (!candidates.length) return -1
  return candidates.sort(
    (a, b) =>
      Math.abs(minutesArr[a] - targetMinutes) -
      Math.abs(minutesArr[b] - targetMinutes),
  )[0]
}

function isOutOfRange(totalMinutes) {
  if (minMinutes.value != null && totalMinutes < minMinutes.value) return true
  if (maxMinutes.value != null && totalMinutes > maxMinutes.value) return true
  return false
}

function applyValue(val24) {
  internalValue.value = val24
  displayValue.value = formatDisplay(val24)
  emit('update:modelValue', val24)
  setInvalid(false)
}

function commitInput() {
  const raw = displayValue.value
  const parsed = parseFlexibleTime(raw)
  if (!raw) {
    internalValue.value = ''
    emit('update:modelValue', '')
    setInvalid(false)
    return
  }
  if (!parsed.valid) {
    emit('input-invalid', raw)
    setInvalid(true)
    return
  }
  if (isOutOfRange(parsed.total)) {
    emit('input-invalid', raw)
    setInvalid(true)
    return
  }
  const normalized = `${parsed.hh24}:${parsed.mm}`
  // Snap if custom disallowed
  if (
    !props.allowCustom &&
    !displayedOptions.value.some((o) => o.value === normalized)
  ) {
    const nearestIdx = findNearestIndex(parsed.total, displayedOptions.value)
    if (nearestIdx > -1)
      return applyValue(displayedOptions.value[nearestIdx].value)
  }
  applyValue(normalized)
}

function select(val, close = props.autoClose) {
  internalValue.value = val
  displayValue.value = formatDisplay(val)
  emit('update:modelValue', val)
  if (close) {
    showOptions.value = false
  }
}

const selectedAndNearest = computed(() => {
  const list = displayedOptions.value
  if (!list.length) return { selected: null, nearest: null }
  const parsedTyped = parseFlexibleTime(displayValue.value)
  const candidate =
    isTyping.value && parsedTyped.valid
      ? `${parsedTyped.hh24}:${parsedTyped.mm}`
      : internalValue.value || null
  if (!candidate) return { selected: null, nearest: null }
  const selected = list.find((o) => o.value === candidate) || null
  if (selected) return { selected, nearest: null }
  const parsed = parseFlexibleTime(candidate)
  if (!parsed.valid) return { selected: null, nearest: null }
  const idx = findNearestIndex(parsed.total, list)
  return { selected: null, nearest: idx > -1 ? list[idx] : null }
})

function buttonClasses(opt, idx) {
  if (idx === highlightIndex.value) return 'bg-surface-gray-3 text-ink-gray-8'
  const { selected, nearest } = selectedAndNearest.value
  if (isTyping.value && !selected) {
    if (nearest && nearest.value === opt.value)
      return 'text-ink-gray-7 italic bg-surface-gray-2'
    return 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8'
  }
  if (selected && selected.value === opt.value)
    return 'bg-surface-gray-3 text-ink-gray-8'
  if (nearest && nearest.value === opt.value)
    return 'text-ink-gray-7 italic bg-surface-gray-2'
  return 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8'
}

watch(
  () => displayedOptions.value,
  () => scheduleScroll(),
)

function scheduleScroll() {
  nextTick(() => {
    if (!panelRef.value) return
    let targetEl = null
    if (highlightIndex.value > -1) {
      targetEl = panelRef.value.querySelector(
        `[data-index="${highlightIndex.value}"]`,
      )
    } else {
      const { selected, nearest } = selectedAndNearest.value
      const target = selected || nearest
      if (target)
        targetEl = panelRef.value.querySelector(
          `[data-value="${target.value}"]`,
        )
    }
    if (!targetEl) return
    const el = targetEl
    if (el)
      el.scrollIntoView({
        block:
          props.scrollMode === 'center'
            ? 'center'
            : props.scrollMode === 'start'
              ? 'start'
              : 'nearest',
      })
  })
}

watch(showOptions, (open) => {
  if (open) {
    emit('open')
    initHighlight()
    scheduleScroll()
  }
})

watch(
  () => displayValue.value,
  () => {
    if (navUpdating) return
    if (showOptions.value) scheduleScroll()
    isTyping.value = true
    highlightIndex.value = -1
  },
)

function initHighlight() {
  // set highlight to selected or nearest
  const { selected, nearest } = selectedAndNearest.value
  const target = selected || nearest
  if (!target) {
    highlightIndex.value = -1
    return
  }
  const idx = displayedOptions.value.findIndex((o) => o.value === target.value)
  highlightIndex.value = idx
}

function moveHighlight(delta) {
  const list = displayedOptions.value
  if (!list.length) return
  if (highlightIndex.value === -1) initHighlight()
  else
    highlightIndex.value =
      (highlightIndex.value + delta + list.length) % list.length
  const opt = list[highlightIndex.value]
  if (opt) {
    navUpdating = true
    internalValue.value = opt.value
    displayValue.value = formatDisplay(opt.value)
    emit('update:modelValue', opt.value)
    nextTick(() => {
      navUpdating = false
    })
  }
  isTyping.value = false
  scheduleScroll()
}

function onArrowDown(togglePopover, isOpen) {
  if (!isOpen) togglePopover()
  else moveHighlight(1)
}
function onArrowUp(togglePopover, isOpen) {
  if (!isOpen) togglePopover()
  else moveHighlight(-1)
}

function onEnter() {
  if (!showOptions.value) {
    commitInput()
    blurInput()
    return
  }
  const parsed = parseFlexibleTime(displayValue.value)
  const normalized = parsed.valid ? `${parsed.hh24}:${parsed.mm}` : null
  const exists = normalized
    ? displayedOptions.value.some((o) => o.value === normalized)
    : false
  if (parsed.valid && (!exists || isTyping.value)) {
    commitInput()
    if (props.autoClose) showOptions.value = false
    blurInput()
    return
  }
  if (highlightIndex.value > -1) {
    const opt = displayedOptions.value[highlightIndex.value]
    if (opt) select(opt.value, true)
  } else {
    commitInput()
    if (props.autoClose) showOptions.value = false
  }
  blurInput()
}

function onClickInput(isOpen, togglePopover) {
  if (!isOpen) {
    togglePopover()
  }
  selectAll()
}

function onFocus() {
  if (!hasSelectedOnFirstClick.value) selectAll()
}

function selectAll() {
  nextTick(() => {
    const el = inputRef.value?.el || inputRef.value
    if (el && el.querySelector) {
      const input = el.querySelector('input') || el
      if (input?.select) input.select()
    } else if (el?.select) {
      el.select()
    }
    hasSelectedOnFirstClick.value = true
  })
}

function blurInput() {
  nextTick(() => {
    const el = inputRef.value?.el || inputRef.value
    if (el && el.querySelector) {
      const input = el.querySelector('input') || el
      input?.blur?.()
    } else if (el?.blur) {
      el.blur()
    }
  })
}

function onEscape() {
  showOptions.value = false
  blurInput()
}

function setInvalid(val) {
  if (invalidState !== val) {
    invalidState = val
    emit('invalid-change', val)
  }
}
</script>
