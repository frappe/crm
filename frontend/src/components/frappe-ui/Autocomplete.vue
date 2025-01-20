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
              class="relative flex h-7 w-full items-center justify-between gap-2 rounded bg-surface-gray-2 px-2 py-1 transition-colors hover:bg-surface-gray-3 border border-transparent focus:border-outline-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
              :class="inputClasses"
              @click="() => togglePopover()"
            >
              <div
                v-if="selectedValue"
                class="flex text-base leading-5 items-center truncate"
              >
                <slot name="prefix" />
                <span class="truncate">
                  {{ displayValue(selectedValue) }}
                </span>
              </div>
              <div
                v-else
                class="absolute text-ink-gray-4 text-left truncate w-full pr-7"
              >
                {{ placeholder || '' }}
              </div>
              <FeatherIcon
                name="chevron-down"
                class="absolute h-4 w-4 text-ink-gray-5 right-2"
                aria-hidden="true"
              />
            </button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen }">
        <div v-show="isOpen">
          <div
            class="relative mt-1 rounded-lg bg-surface-modal text-base shadow-2xl"
          >
            <div class="relative px-1.5 pt-1.5">
              <ComboboxInput
                ref="search"
                class="form-input w-full focus:bg-surface-gray-3 hover:bg-surface-gray-4 text-ink-gray-8"
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
                <FeatherIcon name="x" class="w-4 text-ink-gray-8" />
              </button>
            </div>
            <ComboboxOptions
              class="my-1 max-h-[12rem] overflow-y-auto p-1.5 pt-0"
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
                  class="truncate bg-surface-modal px-2.5 py-1.5 text-sm font-medium text-ink-gray-5"
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
                      'flex cursor-pointer items-center rounded px-2.5 py-1.5 text-base',
                      { 'bg-surface-gray-3': active },
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
                      <div class="flex-1 truncate text-ink-gray-7">
                        {{ option.label }}
                      </div>
                    </slot>
                  </li>
                </ComboboxOption>
              </div>
              <li
                v-if="groups.length == 0"
                class="my-1.5 rounded-md px-2.5 py-1.5 text-base text-ink-gray-5"
              >
                No results found
              </li>
            </ComboboxOptions>
            <div
              v-if="slots.footer"
              class="border-t border-outline-gray-modals p-1.5"
            >
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
      (text || '').toString().toLowerCase().includes(query.value.toLowerCase()),
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
  return props.disabled ? 'text-ink-gray-5' : 'text-ink-gray-8'
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
      'border border-gray-100 bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3',
    outline:
      'border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3',
    disabled: [
      'border bg-surface-menu-bar placeholder-ink-gray-3',
      props.variant === 'outline'
        ? 'border-outline-gray-2'
        : 'border-transparent',
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
