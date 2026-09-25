<template>
  <div class="relative w-full">
    <div
      class="flex h-7 items-center rounded border border-outline-gray-2 bg-surface-gray-2 text-base transition-colors hover:border-outline-gray-3 focus-within:bg-surface-base focus-within:border-outline-gray-4 focus-within:shadow-sm"
      :class="{
        '!border-outline-red-3 focus-within:!border-outline-red-3':
          Boolean(errorMessage),
        '!bg-surface-gray-1 !border-transparent opacity-60 pointer-events-none':
          disabled,
      }"
    >
      <!-- Country Code Popover Selector -->
      <Popover
        placement="bottom-start"
        class="shrink-0 h-full"
        @open="searchQuery = ''"
      >
        <template #target="{ togglePopover }">
          <button
            type="button"
            class="flex h-full items-center gap-1 px-2 text-ink-gray-8 hover:bg-surface-gray-3 rounded-l transition-colors cursor-pointer border-r border-outline-gray-2 outline-none select-none text-xs font-medium"
            :disabled="disabled"
            :title="selectedCountry?.country || __('Select country')"
            @click="togglePopover"
          >
            <span class="text-sm leading-none shrink-0">{{
              getCountryEmoji(selectedCountry?.code)
            }}</span>
            <span class="font-mono text-xs">{{
              selectedCountry?.isd || '+1'
            }}</span>
            <svg
              class="w-3 h-3 text-ink-gray-5 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </template>
        <template #body="{ isOpen, togglePopover }">
          <div
            v-if="isOpen"
            class="w-64 rounded-lg bg-surface-elevation-2 p-2 shadow-2xl ring-1 ring-black ring-opacity-5 border border-outline-gray-2 text-ink-gray-8 z-50 my-1"
          >
            <input
              v-focus
              v-model="searchQuery"
              type="text"
              class="w-full rounded border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-1.5 text-xs text-ink-gray-8 placeholder:text-ink-gray-4 outline-none focus:border-outline-gray-4 focus:ring-1 focus:ring-outline-gray-4 mb-1.5"
              :placeholder="__('Search country or code...')"
              @click.stop
            />
            <div
              class="max-h-52 overflow-y-auto divide-y divide-outline-gray-1"
            >
              <button
                v-for="country in filteredCountries"
                :key="country.code + country.country"
                type="button"
                class="flex items-center justify-between w-full px-2 py-1.5 text-xs text-left rounded hover:bg-surface-gray-3 cursor-pointer transition-colors"
                :class="{
                  'bg-surface-gray-3 font-medium text-ink-gray-9':
                    country.code === selectedCountry?.code,
                }"
                @click="onSelectCountry(country, togglePopover)"
              >
                <div class="flex items-center gap-2 truncate pr-2">
                  <span class="text-sm leading-none shrink-0">{{
                    getCountryEmoji(country.code)
                  }}</span>
                  <span class="truncate">{{ country.country }}</span>
                </div>
                <span class="text-ink-gray-5 shrink-0 font-mono">{{
                  country.isd
                }}</span>
              </button>
              <div
                v-if="!filteredCountries.length"
                class="py-3 text-center text-xs text-ink-gray-5"
              >
                {{ __('No countries found') }}
              </div>
            </div>
          </div>
        </template>
      </Popover>

      <!-- Phone Number Input -->
      <input
        ref="phoneInputRef"
        type="tel"
        :value="phonePart"
        :disabled="disabled"
        :placeholder="placeholder || __('Enter phone number')"
        class="h-full w-full flex-1 bg-transparent px-2.5 text-base text-ink-gray-8 placeholder-ink-gray-4 outline-none border-none focus:ring-0"
        @input="handleInput"
        @change="handleChange"
      />
    </div>

    <!-- Error or description message -->
    <p v-if="errorMessage" class="mt-1 text-xs text-ink-red-6">
      {{ errorMessage }}
    </p>
    <p v-else-if="description" class="mt-1 text-xs text-ink-gray-5">
      {{ description }}
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Popover, createResource } from 'frappe-ui'
import { validatePhone } from '@/utils'
import {
  formatCountryList,
  getCountryEmoji,
  parsePhoneNumber,
  formatPhoneNumber,
} from '@/utils/countryCodes'

const props = defineProps({
  value: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  description: { type: String, default: '' },
  error: { type: String, default: '' },
  defaultCountry: { type: [String, Object], default: '' },
})

const emit = defineEmits(['change', 'update:modelValue'])

const phoneInputRef = ref(null)
const searchQuery = ref('')

const vFocus = {
  mounted: (el) => el.focus(),
}

const countryInfoResource = createResource({
  url: 'frappe.geo.country_info.get_country_timezone_info',
  cache: 'country_info',
  auto: true,
  transform: (data) => formatCountryList(data?.country_info || {}),
})

const countries = computed(() => countryInfoResource.data || [])

const parsed = parsePhoneNumber(
  props.value,
  props.defaultCountry,
  countries.value,
)
const selectedCountry = ref(parsed.country)
const phonePart = ref(parsed.phone)

watch(
  () => props.value,
  (newVal) => {
    const p = parsePhoneNumber(
      newVal,
      selectedCountry.value || props.defaultCountry,
      countries.value,
    )
    selectedCountry.value = p.country
    phonePart.value = p.phone
  },
)

watch(
  countries,
  (list) => {
    if (list?.length) {
      const p = parsePhoneNumber(
        props.value,
        selectedCountry.value || props.defaultCountry,
        list,
      )
      selectedCountry.value = p.country
      if (props.value != null && props.value !== '') {
        phonePart.value = p.phone
      }
    }
  },
  { immediate: true },
)

const filteredCountries = computed(() => {
  if (!searchQuery.value.trim()) return countries.value
  const q = searchQuery.value.toLowerCase().trim()
  return countries.value.filter(
    (c) =>
      c.country.toLowerCase().includes(q) ||
      c.isd.includes(q) ||
      c.code.toLowerCase().includes(q),
  )
})

const errorMessage = computed(() => {
  if (props.error) return props.error
  if (!phonePart.value) return ''
  const fullVal = formatPhoneNumber(selectedCountry.value, phonePart.value)
  if (!validatePhone(fullVal)) {
    return __('Enter a valid phone number')
  }
  return ''
})

function onSelectCountry(country, togglePopover) {
  selectedCountry.value = country
  searchQuery.value = ''
  togglePopover?.()
  nextTick(() => {
    phoneInputRef.value?.focus()
  })
  if (phonePart.value) {
    const formatted = formatPhoneNumber(selectedCountry.value, phonePart.value)
    emit('change', formatted)
    emit('update:modelValue', formatted)
  }
}

function handleInput(e) {
  let val = e.target.value || ''
  // If user pasted or typed full international number starting with '+'
  if (val.startsWith('+')) {
    const p = parsePhoneNumber(val, selectedCountry.value, countries.value)
    selectedCountry.value = p.country
    phonePart.value = p.phone
  } else {
    phonePart.value = val
  }
  const formatted = formatPhoneNumber(selectedCountry.value, phonePart.value)
  emit('update:modelValue', formatted)
}

function handleChange() {
  const formatted = formatPhoneNumber(selectedCountry.value, phonePart.value)
  emit('change', formatted)
  emit('update:modelValue', formatted)
}
</script>
