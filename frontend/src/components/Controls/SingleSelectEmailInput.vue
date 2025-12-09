<template>
  <div>
    <Combobox v-model="selectedValue" nullable>
      <Popover class="w-full" v-model:show="showOptions">
        <template #target="{ togglePopover }">
          <ComboboxInput
            ref="search"
            class="search-input form-input w-full border-none focus:border-none focus:!shadow-none focus-visible:!ring-0"
            :class="[
              variant == 'ghost'
                ? 'bg-surface-white hover:bg-surface-white'
                : 'bg-surface-gray-2 hover:bg-surface-gray-3',
              inputClass,
            ]"
            :placeholder="placeholder"
            type="text"
            :value="displayValue"
            @change="
              (e) => {
                query = e.target.value
                showOptions = true
              }
            "
            autocomplete="off"
            @focus="() => togglePopover()"
            readonly
          />
        </template>
        <template #body="{ isOpen }">
          <div v-show="isOpen">
            <div
              class="mt-1 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
            >
              <ComboboxOptions
                class="p-1.5 max-h-[12rem] overflow-y-auto"
                static
              >
                <div
                  v-if="!options.length"
                  class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                >
                  {{ __('No email accounts found') }}
                </div>
                <ComboboxOption
                  v-for="option in options"
                  :key="option.value"
                  :value="option"
                  v-slot="{ active }"
                >
                  <li
                    :class="[
                      'flex cursor-pointer items-center rounded px-2 py-1 text-base',
                      { 'bg-surface-gray-3': active },
                    ]"
                  >
                    <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                      <div class="text-base font-medium">
                        {{ option.label }}
                      </div>
                    </div>
                  </li>
                </ComboboxOption>
              </ComboboxOptions>
            </div>
          </div>
        </template>
      </Popover>
    </Combobox>
  </div>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/vue'
import Popover from '@/components/frappe-ui/Popover.vue'
import { createResource } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'subtle',
  },
  placeholder: {
    type: String,
    default: __('Select email account'),
  },
  inputClass: {
    type: String,
    default: '',
  },
})

const modelValue = defineModel()

const search = ref(null)
const query = ref('')
const showOptions = ref(false)

const emailAccounts = createResource({
  url: 'crm.api.settings.get_outgoing_email_accounts',
  auto: true,
  cache: 'user-outgoing-email-accounts',
})

const options = computed(() => {
  if (!emailAccounts.data) return []
  
  // Filter options based on query
  if (query.value) {
    return emailAccounts.data.filter((option) =>
      option.label.toLowerCase().includes(query.value.toLowerCase())
    )
  }
  return emailAccounts.data
})

const displayValue = computed(() => {
  if (!modelValue.value) return ''
  const selected = emailAccounts.data?.find(
    (opt) => opt.value === modelValue.value
  )
  return selected ? selected.label : ''
})

const selectedValue = computed({
  get: () => {
    if (!modelValue.value) return null
    return emailAccounts.data?.find((opt) => opt.value === modelValue.value)
  },
  set: (val) => {
    query.value = ''
    if (val) {
      showOptions.value = false
      modelValue.value = val.value
    } else {
      modelValue.value = null
    }
  },
})

// Auto-select first email account if none selected and accounts are loaded
watch(
  () => emailAccounts.data,
  (accounts) => {
    if (accounts && accounts.length > 0 && !modelValue.value) {
      modelValue.value = accounts[0].value
    }
  },
  { immediate: true }
)

function setFocus() {
  search.value?.$el?.focus()
}

defineExpose({ setFocus })
</script>

