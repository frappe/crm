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
        class="mt-2 min-w-40 max-h-72 overflow-hidden overflow-y-auto divide-y divide-outline-gray-modals rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none [&>div]:focus-visible:ring-0"
        :class="{
          'mt-2': ['bottom', 'left', 'right'].includes(placement),
          'ml-2': placement == 'right-start',
        }"
      >
        <MenuItems class="p-1" ref="menu">
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

  if (timeMap[time]) {
    time = timeMap[time]
  } else {
    const [hour, minute] = time.split(':')
    const ampm = hour >= 12 ? 'pm' : 'am'
    const formattedHour = hour % 12 || 12
    time = `${formattedHour}:${minute} ${ampm}`
  }

  return time
})

const options = () => {
  let timeOptions = []
  for (const [key, value] of Object.entries(timeMap)) {
    timeOptions.push({
      label: value,
      value: key,
      onClick: () => emitUpdate(key),
      isSelected: () => {
        let isSelected = isSelectedOrNearestOption()
        return isSelected?.value === key && !isSelected?.isNearest
      },
    })
  }
  return timeOptions
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
    (option) => option.label === selectedTime,
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

const timeMap = {
  '00:00': '12:00 am',
  '00:30': '12:30 am',
  '01:00': '1:00 am',
  '01:30': '1:30 am',
  '02:00': '2:00 am',
  '02:30': '2:30 am',
  '03:00': '3:00 am',
  '03:30': '3:30 am',
  '04:00': '4:00 am',
  '04:30': '4:30 am',
  '05:00': '5:00 am',
  '05:30': '5:30 am',
  '06:00': '6:00 am',
  '06:30': '6:30 am',
  '07:00': '7:00 am',
  '07:30': '7:30 am',
  '08:00': '8:00 am',
  '08:30': '8:30 am',
  '09:00': '9:00 am',
  '09:30': '9:30 am',
  '10:00': '10:00 am',
  '10:30': '10:30 am',
  '11:00': '11:00 am',
  '11:30': '11:30 am',
  '12:00': '12:00 pm',
  '12:30': '12:30 pm',
  '13:00': '1:00 pm',
  '13:30': '1:30 pm',
  '14:00': '2:00 pm',
  '14:30': '2:30 pm',
  '15:00': '3:00 pm',
  '15:30': '3:30 pm',
  '16:00': '4:00 pm',
  '16:30': '4:30 pm',
  '17:00': '5:00 pm',
  '17:30': '5:30 pm',
  '18:00': '6:00 pm',
  '18:30': '6:30 pm',
  '19:00': '7:00 pm',
  '19:30': '7:30 pm',
  '20:00': '8:00 pm',
  '20:30': '8:30 pm',
  '21:00': '9:00 pm',
  '21:30': '9:30 pm',
  '22:00': '10:00 pm',
  '22:30': '10:30 pm',
  '23:00': '11:00 pm',
  '23:30': '11:30 pm',
}
</script>
