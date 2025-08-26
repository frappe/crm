<template>
  <Dropdown :options="options()">
    <template #default="{ open, togglePopover }">
      <slot
        v-bind="{
          emitUpdate,
          timeValue,
          isSelectedOrNearestOption,
          updateScroll,
        }"
      >
        <TextInput
          :variant="variant"
          class="text-sm"
          v-bind="$attrs"
          type="text"
          :value="timeValue"
          :placeholder="placeholder"
          @change="(e) => emitUpdate(e.target.value)"
          @keydown.enter.prevent="(e) => emitUpdate(e.target.value)"
        >
          <template #prefix v-if="$slots.prefix">
            <slot name="prefix" />
          </template>
          <template #suffix v-if="$slots.suffix">
            <slot name="suffix" v-bind="{ togglePopover }" />
          </template>
        </TextInput>
      </slot>
    </template>
    <template #body>
      <div
        class="mt-2 min-w-40 max-h-72 overflow-hidden overflow-y-auto divide-y divide-outline-gray-modals rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5"
        :class="{
          'mt-2': ['bottom', 'left', 'right'].includes(placement),
          'ml-2': placement == 'right-start',
        }"
      >
        <MenuItems class="p-1 focus-visible:outline-none" ref="menu">
          <MenuItem
            v-for="option in options()"
            :key="option.value"
            :data-value="option.value"
          >
            <slot
              name="menu-item"
              v-bind="{ option, isSelectedOrNearestOption, updateScroll }"
            >
              <button
                :class="[
                  option.isSelected()
                    ? 'bg-surface-gray-3 text-ink-gray-8'
                    : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8',
                  'group flex h-7 w-full items-center rounded px-2 text-base ',
                ]"
                @click="option.onClick"
              >
                {{ option.label }}
              </button>
            </slot>
          </MenuItem>
        </MenuItems>
      </div>
    </template>
  </Dropdown>
</template>

<script setup>
import { TextInput } from 'frappe-ui'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import { allTimeSlots } from '@/components/Calendar/utils'
import { MenuItems, MenuItem } from '@headlessui/vue'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  value: {
    type: String,
    default: '',
  },
  modelValue: {
    type: String,
    default: '',
  },
  variant: {
    type: String,
    default: 'subtle',
  },
  placeholder: {
    type: String,
    default: 'Select Time',
  },
  placement: {
    type: String,
    default: 'bottom',
  },
  customOptions: {
    type: Array,
    default: () => [],
  },
})
const emit = defineEmits(['update:modelValue'])

const emitUpdate = (value) => {
  emit('update:modelValue', convertTo24HourFormat(value))
}

const timeValue = computed(() => {
  let time = props.value ? props.value : props.modelValue

  if (!time) return ''

  if (time && time.length > 5) {
    time = time.substring(0, 5)
  }

  // Try to find a matching option (value is always in 24h format HH:MM)
  const match = options().find((o) => o.value === time)
  if (match) return match.label.split(' (')[0]

  // Fallback: format manually if the value isn't part of provided options
  const [hourStr, minute] = time.split(':')
  if (hourStr !== undefined && minute !== undefined) {
    const hourNum = parseInt(hourStr)
    if (!isNaN(hourNum)) {
      const ampm = hourNum >= 12 ? 'pm' : 'am'
      const formattedHour = hourNum % 12 || 12
      return `${formattedHour}:${minute} ${ampm}`
    }
  }
  return time
})

const options = () => {
  let timeOptions = []

  const _options = props.customOptions.length
    ? props.customOptions
    : allTimeSlots()

  for (const option of _options) {
    timeOptions.push(timeObj(option.label, option.value))
  }

  return timeOptions
}

function timeObj(label, value) {
  return {
    label,
    value,
    onClick: () => emitUpdate(value),
    isSelected: () => {
      let isSelected = isSelectedOrNearestOption()
      return isSelected?.value === value && !isSelected?.isNearest
    },
  }
}

const menu = ref(null)

watch(
  () => menu.value?.el,
  (newValue) => {
    if (newValue) {
      updateScroll(newValue)
    }
  },
)

function convertTo24HourFormat(time) {
  if (time && time.length > 5) {
    time = time.trim().replace(' ', '')
    const ampm = time.slice(-2)
    time = time.slice(0, -2)
    let [hour, minute] = time.split(':')
    if (ampm === 'pm' && parseInt(hour) < 12) {
      hour = parseInt(hour) + 12
    } else if (ampm === 'am' && hour == 12) {
      hour = 0
    }
    time = `${hour.toString().padStart(2, '0')}:${minute}`
  }
  return time
}

function isSelectedOrNearestOption() {
  const selectedTime = timeValue.value
  const selectedOption = options().find(
    (option) => option.label.split(' (')[0] === selectedTime,
  )

  if (selectedOption) {
    return {
      ...selectedOption,
      isNearest: false,
    }
  }

  //   remove hour from timeValue
  let time = convertTo24HourFormat(timeValue.value)
  const [hour, minute] = time.split(':')

  //   find nearest option where hour is same
  const nearestOption = options().find((option) => {
    const [optionHour] = option.value.split(':')
    return optionHour === hour
  })

  if (nearestOption) {
    return {
      ...nearestOption,
      isNearest: true,
    }
  }

  return null
}

function updateScroll(el) {
  const selectedOption = options().find(
    (option) => option.label === timeValue.value,
  )

  let selectedTimeObj = selectedOption ? { ...selectedOption } : null

  if (!selectedTimeObj) {
    selectedTimeObj = isSelectedOrNearestOption()
  }

  if (selectedTimeObj) {
    const selectedElement = el.querySelector(
      `[data-value="${selectedTimeObj.value}"]`,
    )

    if (selectedElement) {
      selectedElement.scrollIntoView({
        inline: 'start',
        block: 'start',
      })
    }
  }
}
</script>
