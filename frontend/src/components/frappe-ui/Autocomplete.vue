<template>
  <Combobox v-model="selectedValue" nullable v-slot="{ open: isComboboxOpen }">
    <Popover class="w-full" v-model:show="showOptions">
      <template #target="{ open: openPopover, togglePopover }">
        <slot
          name="target"
          v-bind="{
            open: openPopover,
            togglePopover,
            isOpen: showOptions,
            selectedValue,
            displayValue,
          }"
        >
          <div class="w-full">
            <button
              class="flex w-full items-center justify-between focus:outline-none"
              :class="inputClasses"
              @click="() => togglePopover()"
            >
              <div class="flex items-center">
                <slot name="prefix" />
                <span
                  class="overflow-hidden text-ellipsis whitespace-nowrap text-base leading-5"
                  v-if="selectedValue"
                >
                  {{ displayValue(selectedValue) }}
                </span>
                <span class="text-base leading-5 text-gray-500" v-else>
                  {{ placeholder || '' }}
                </span>
              </div>
              <FeatherIcon
                name="chevron-down"
                class="h-4 w-4 text-gray-600"
                aria-hidden="true"
              />
            </button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen }">
        <div v-show="isOpen">
          <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl">
            <div class="relative px-1.5 pt-0.5">
              <ComboboxInput
                ref="search"
                class="form-input w-full"
                type="text"
                @change="
                  (e) => {
                    query = e.target.value
                  }
                "
                :value="query"
                autocomplete="off"
                placeholder="Search"
              />
              <button
                class="absolute right-1.5 inline-flex h-7 w-7 items-center justify-center"
                @click="selectedValue = null"
              >
                <FeatherIcon name="x" class="w-4" />
              </button>
            </div>
            <ComboboxOptions
              class="my-1 max-h-[12rem] overflow-y-auto px-1.5"
              static
            >
              <div
                class="mt-1.5"
                v-for="group in groups"
                :key="group.key"
                v-show="group.items.length > 0"
              >
                <div
                  v-if="group.group && !group.hideLabel"
                  class="px-2.5 py-1.5 text-sm font-medium text-gray-500"
                >
                  {{ group.group }}
                </div>
                <ComboboxOption
                  as="template"
                  v-for="option in group.items"
                  :key="option.value"
                  :value="option"
                  v-slot="{ active, selected }"
                >
                  <li
                    :class="[
                      'flex items-center rounded px-2.5 py-1.5 text-base',
                      { 'bg-gray-100': active },
                    ]"
                  >
                    <slot
                      name="item-prefix"
                      v-bind="{ active, selected, option }"
                    />
                    <slot
                      name="item-label"
                      v-bind="{ active, selected, option }"
                    >
                      {{ option.label }}
                    </slot>
                  </li>
                </ComboboxOption>
              </div>
              <li
                v-if="groups.length == 0"
                class="mt-1.5 rounded-md px-2.5 py-1.5 text-base text-gray-600"
              >
                No results found
              </li>
            </ComboboxOptions>
            <div v-if="slots.footer" class="border-t p-1.5 pb-0.5">
              <slot
                name="footer"
                v-bind="{ value: search?.el._value, close }"
              ></slot>
            </div>
          </div>
        </div>
      </template>
    </Popover>
  </Combobox>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/vue'
import { Popover, Button, FeatherIcon } from 'frappe-ui'
import { ref, computed, useAttrs, useSlots, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  size: {
    type: String,
    default: 'md',
  },
  variant: {
    type: String,
    default: 'subtle',
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  filterable: {
    type: Boolean,
    default: true,
  },
})
const emit = defineEmits(['update:modelValue', 'update:query', 'change'])

const query = ref('')
const showOptions = ref(false)
const search = ref(null)

const attrs = useAttrs()
const slots = useSlots()

const valuePropPassed = computed(() => 'value' in attrs)

const selectedValue = computed({
  get() {
    return valuePropPassed.value ? attrs.value : props.modelValue
  },
  set(val) {
    query.value = ''
    if (val) {
      showOptions.value = false
    }
    emit(valuePropPassed.value ? 'change' : 'update:modelValue', val)
  },
})

function close() {
  showOptions.value = false
}

const groups = computed(() => {
  if (!props.options || props.options.length == 0) return []

  let groups = props.options[0]?.group
    ? props.options
    : [{ group: '', items: props.options }]

  return groups
    .map((group, i) => {
      return {
        key: i,
        group: group.group,
        hideLabel: group.hideLabel || false,
        items: props.filterable ? filterOptions(group.items) : group.items,
      }
    })
    .filter((group) => group.items.length > 0)
})

function filterOptions(options) {
  if (!query.value) {
    return options
  }
  return options.filter((option) => {
    let searchTexts = [option.label, option.value]
    return searchTexts.some((text) =>
      (text || '').toString().toLowerCase().includes(query.value.toLowerCase())
    )
  })
}

function displayValue(option) {
  if (typeof option === 'string') {
    let allOptions = groups.value.flatMap((group) => group.items)
    let selectedOption = allOptions.find((o) => o.value === option)
    return selectedOption?.label || option
  }
  return option?.label
}

watch(query, (q) => {
  emit('update:query', q)
})

watch(showOptions, (val) => {
  if (val) {
    nextTick(() => {
      search.value.el.focus()
    })
  }
})

const textColor = computed(() => {
  return props.disabled ? 'text-gray-600' : 'text-gray-800'
})

const inputClasses = computed(() => {
  let sizeClasses = {
    sm: 'text-base rounded h-7',
    md: 'text-base rounded h-8',
    lg: 'text-lg rounded-md h-10',
    xl: 'text-xl rounded-md h-10',
  }[props.size]

  let paddingClasses = {
    sm: 'py-1.5 px-2',
    md: 'py-1.5 px-2.5',
    lg: 'py-1.5 px-3',
    xl: 'py-1.5 px-3',
  }[props.size]

  let variant = props.disabled ? 'disabled' : props.variant
  let variantClasses = {
    subtle:
      'border border-gray-100 bg-gray-100 placeholder-gray-500 hover:border-gray-200 hover:bg-gray-200 focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400',
    outline:
      'border border-gray-300 bg-white placeholder-gray-500 hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400',
    disabled: [
      'border bg-gray-50 placeholder-gray-400',
      props.variant === 'outline' ? 'border-gray-300' : 'border-transparent',
    ],
  }[variant]

  return [
    sizeClasses,
    paddingClasses,
    variantClasses,
    textColor.value,
    'transition-colors w-full',
  ]
})

defineExpose({ query })
</script>
