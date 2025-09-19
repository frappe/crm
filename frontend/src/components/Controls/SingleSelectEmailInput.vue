<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        v-if="selectedEmail"
        :key="selectedEmail"
        :label="selectedEmail"
        theme="gray"
        variant="subtle"
        :class="{
          'rounded bg-surface-white hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4':
            variant === 'subtle',
        }"
      >
        <template #suffix>
          <FeatherIcon class="h-3.5" name="x" @click.stop="clearSelection" />
        </template>
      </Button>
      <div class="flex-1">
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
                :placeholder="selectedEmail ? '' : placeholder"
                type="text"
                :value="query"
                @change="
                  (e) => {
                    query = e.target.value
                    showOptions = true
                  }
                "
                autocomplete="off"
                @focus="() => togglePopover()"
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
                      v-if="!filteredOptions.length"
                      class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                    >
                      <FeatherIcon name="search" class="h-4" />
                      {{ __('No email accounts found') }}
                    </div>
                    <ComboboxOption
                      v-for="option in filteredOptions"
                      :key="option"
                      :value="option"
                      v-slot="{ active }"
                    >
                      <li
                        :class="[
                          'flex cursor-pointer items-center rounded px-2 py-1 text-base',
                          { 'bg-surface-gray-3': active },
                        ]"
                      >
                        <UserAvatar class="mr-2" :user="option" size="lg" />
                        <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                          <div class="text-base font-medium">
                            {{ option }}
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
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
    <div
      v-if="info"
      class="whitespace-pre-line text-sm text-ink-blue-3 mt-2 pl-2"
    >
      {{ info }}
    </div>
  </div>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { Popover } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'subtle',
  },
  placeholder: {
    type: String,
    default: 'Select an email',
  },
  inputClass: {
    type: String,
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  validate: {
    type: Function,
    default: null,
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an invalid email address`,
  },
})

const values = defineModel()

const search = ref(null)
const error = ref(null)
const info = ref(null)
const query = ref('')
const showOptions = ref(false)

const selectedEmail = computed(() => {
  return values.value && values.value.length > 0 ? values.value[0] : null
})

const selectedValue = computed({
  get: () => query.value || '',
  set: (val) => {
    query.value = ''
    if (val) {
      showOptions.value = false
      selectEmail(val)
    }
  },
})

const filteredOptions = computed(() => {
  if (!query.value) return props.options
  return props.options.filter((option) =>
    option.toLowerCase().includes(query.value.toLowerCase()),
  )
})

const selectEmail = (email) => {
  error.value = null
  info.value = null

  if (email) {
    if (props.validate && !props.validate(email)) {
      error.value = props.errorMessage(email)
      query.value = email
      return
    }

    values.value = [email]

    // Check if email already exists
    if (selectedEmail.value && selectedEmail.value === email) {
      info.value = __('email already selected')
    }
  }
}

const clearSelection = () => {
  // Prevent clearing
  if (!selectedEmail.value) {
    error.value = __('Please select an email account')
    return
  }
  values.value = []
  error.value = __('Please select an email account')
  info.value = null
  nextTick(() => {
    setFocus()
  })
}

// Validation: Ensure not empty before using
watch(
  values,
  (newValue) => {
    if (!newValue || newValue.length === 0) {
      error.value = __('Please select an email account')
    } else {
      error.value = null
    }
  },
  { deep: true, immediate: true },
)

function setFocus() {
  search.value.$el.focus()
}

defineExpose({ setFocus })
</script>
