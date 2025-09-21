<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        ref="emails"
        v-for="value in values"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        :class="{
          'rounded bg-surface-white hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4':
            variant === 'subtle',
        }"
        @keydown.delete.capture.stop="removeLastValue"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="removeValue(value)"
          />
        </template>
      </Button>
      <div class="flex-1">
        <ComboboxRoot
          :model-value="tempSelection"
          :open="showOptions"
          @update:open="(o) => (showOptions = o)"
          @update:modelValue="onSelect"
          :ignore-filter="true"
        >
          <ComboboxAnchor
            class="flex h-7 max-w-full w-auto items-center gap-2 rounded px-2 py-1 border border-transparent"
            :class="[
              variant == 'ghost'
                ? 'bg-surface-white hover:bg-surface-white'
                : 'bg-surface-gray-2 hover:bg-surface-gray-3',
              inputClass,
            ]"
          >
            <ComboboxInput
              ref="search"
              :value="query"
              autocomplete="off"
              class="bg-transparent p-0 outline-none border-0 text-base text-ink-gray-8 h-full placeholder:text-ink-gray-4 w-full focus:outline-none focus:ring-0 focus:border-0"
              :placeholder="placeholder"
              @focus="showOptions = true"
              @input="onInput"
              @keydown.delete.capture.stop="removeLastValue"
              @keydown.enter.prevent="handleEnter"
            />
          </ComboboxAnchor>
          <ComboboxPortal>
            <ComboboxContent
              class="z-10 mt-1 min-w-48 w-auto max-w-96 bg-surface-modal overflow-hidden rounded-lg shadow-2xl ring-1 ring-black ring-opacity-5"
              position="popper"
              :align="'start'"
              @openAutoFocus.prevent
              @closeAutoFocus.prevent
            >
              <ComboboxViewport class="max-h-60 overflow-auto p-1.5">
                <ComboboxEmpty
                  class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                >
                  <FeatherIcon
                    v-if="showSearchIcon"
                    name="search"
                    class="h-4"
                  />
                  {{ emptyStateText }}
                </ComboboxEmpty>
                <ComboboxItem
                  v-for="option in options"
                  :key="option.value"
                  :value="option.value"
                  class="text-base leading-none text-ink-gray-7 rounded flex items-center px-2 py-1 relative select-none data-[highlighted]:outline-none data-[highlighted]:bg-surface-gray-3 cursor-pointer"
                  @mousedown.prevent="onSelect(option.value)"
                >
                  <UserAvatar class="mr-2" :user="option.value" size="lg" />
                  <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                    <div class="text-base font-medium">{{ option.label }}</div>
                    <div class="text-sm text-ink-gray-5">
                      {{ option.value }}
                    </div>
                  </div>
                </ComboboxItem>
              </ComboboxViewport>
            </ComboboxContent>
          </ComboboxPortal>
        </ComboboxRoot>
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
// Generic multi-source (users / contacts / free) multi-select email-like input
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { createResource } from 'frappe-ui'
import {
  ComboboxRoot,
  ComboboxAnchor,
  ComboboxInput,
  ComboboxPortal,
  ComboboxContent,
  ComboboxViewport,
  ComboboxItem,
  ComboboxEmpty,
} from 'reka-ui'
import { ref, computed, nextTick } from 'vue'
import { watchDebounced } from '@vueuse/core'

const props = defineProps({
  // Behaviour
  mode: { type: String, default: null }, // 'users' | 'contacts' | 'free' (fallback to legacy flags)
  fetchUsers: { type: Boolean, default: false },
  fetchContacts: { type: Boolean, default: false },
  existingEmails: { type: Array, default: () => [] },
  validate: { type: Function, default: null },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
  emptyPlaceholder: { type: String, default: __('No results found') },
  // UI
  variant: { type: String, default: 'subtle' },
  placeholder: { type: String, default: '' },
  inputClass: { type: String, default: '' },
})

// v-model values
const values = defineModel()

// Determine effective mode (backwards compatibility with old components)
const effectiveMode = computed(() => {
  if (props.mode) return props.mode
  if (props.fetchUsers) return 'users'
  if (props.fetchContacts) return 'contacts'
  return 'free'
})

// Common state
const emails = ref([])
const search = ref(null)
const error = ref(null)
const info = ref(null)
const query = ref('')
const showOptions = ref(false)
const tempSelection = ref(null)

// Users data
const { users } = usersStore()

// Contacts resource (only if needed)
const filterOptions = ref(null)
const lastLoadedQuery = ref('')

if (effectiveMode.value === 'contacts') {
  filterOptions.value = createResource({
    url: 'crm.api.contact.search_emails',
    method: 'POST',
    cache: ['ContactEmails'],
    params: { txt: '' },
    transform: (data) => {
      let allData = (data || []).map((option) => {
        const fullName = option[0]
        const email = option[1]
        const name = option[2]
        return { label: fullName || name || email, value: email }
      })
      if (props.existingEmails?.length) {
        allData = allData.filter((o) => !props.existingEmails.includes(o.value))
      }
      return allData
    },
  })

  watchDebounced(
    query,
    (val) => {
      val = val || ''
      if (lastLoadedQuery.value === val && options.value?.length) return
      lastLoadedQuery.value = val
      reload(val)
    },
    { debounce: 300, immediate: true },
  )
}

function reload(val) {
  if (effectiveMode.value !== 'contacts' || !filterOptions.value) return
  filterOptions.value.update({ params: { txt: val } })
  filterOptions.value.reload()
}

// Options computed
const options = computed(() => {
  const mode = effectiveMode.value
  if (mode === 'users') {
    let list = users?.data?.allUsers || []
    list = list.map((u) => ({
      label: u.full_name || u.name || u.email,
      value: u.email,
    }))
    if (props.existingEmails?.length) {
      list = list.filter((o) => !props.existingEmails.includes(o.value))
    }
    if (query.value) {
      const q = query.value.toLowerCase()
      list = list.filter(
        (o) =>
          o.label?.toLowerCase().includes(q) ||
          o.value?.toLowerCase().includes(q),
      )
    }
    return list
  }
  if (mode === 'contacts') {
    const list = filterOptions.value?.data ? [...filterOptions.value.data] : []
    if (!list.length && query.value) {
      list.push({ label: query.value, value: query.value })
    }
    return list
  }
  // Free / manual mode
  return query.value ? [{ label: query.value, value: query.value }] : []
})

const showSearchIcon = computed(() => effectiveMode.value !== 'free')
const emptyStateText = computed(() => {
  if (effectiveMode.value === 'free') return __(props.emptyPlaceholder)
  return options.value.length ? '' : __(props.emptyPlaceholder)
})

function addValue(input) {
  if (!input) return
  error.value = null
  info.value = null
  const parts = input
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean)
  for (const email of parts) {
    if (values.value?.includes(email)) {
      info.value = __('email already exists')
      continue
    }
    if (props.validate && !props.validate(email)) {
      error.value = props.errorMessage(email)
      query.value = email
      break
    }
    if (!values.value) values.value = [email]
    else values.value.push(email)
  }
}

function removeValue(value) {
  values.value = values.value.filter((v) => v !== value)
}

function removeLastValue() {
  if (query.value) return
  let emailRef = emails.value[emails.value.length - 1]?.rootRef
  if (document.activeElement === emailRef) {
    values.value.pop()
    nextTick(() => {
      if (values.value.length) {
        emailRef = emails.value[emails.value.length - 1].rootRef
        emailRef?.focus()
      } else {
        setFocus()
      }
    })
  } else {
    emailRef?.focus()
  }
}

function setFocus() {
  search.value?.focus?.()
}

defineExpose({ setFocus })

function onInput(e) {
  query.value = e.target.value
  showOptions.value = true
}

function onSelect(val) {
  if (!val) return
  addValue(val)
  if (!error.value) {
    query.value = ''
    tempSelection.value = null
    showOptions.value = false
    nextTick(() => setFocus())
  }
}

function handleEnter() {
  if (query.value) onSelect(query.value)
}
</script>
