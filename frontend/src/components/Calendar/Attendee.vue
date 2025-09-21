<template>
  <div>
    <!-- Combobox Input -->
    <div class="flex items-center w-full text-ink-gray-8 [&>div]:w-full">
      <ComboboxRoot
        :model-value="tempSelection"
        :open="showOptions"
        @update:open="(o) => (showOptions = o)"
        @update:modelValue="onSelect"
        :ignore-filter="true"
      >
        <ComboboxAnchor
          class="flex w-full text-base items-center gap-1 rounded border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 px-2 py-1"
          :class="[size === 'sm' ? 'h-7' : 'h-8 ', inputClass]"
          @click="showOptions = true"
        >
          <ComboboxInput
            ref="search"
            autocomplete="off"
            class="bg-transparent p-0 outline-none border-0 text-base text-ink-gray-8 h-full placeholder:text-ink-gray-4 w-full focus:outline-none focus:ring-0 focus:border-0"
            :placeholder="placeholder"
            :value="query"
            @input="onInput"
            @keydown.enter.prevent="handleEnter"
            @keydown.escape.stop="showOptions = false"
          />
          <FeatherIcon
            name="chevron-down"
            class="h-4 text-ink-gray-5 cursor-pointer"
            @click.stop="showOptions = !showOptions"
          />
        </ComboboxAnchor>
        <ComboboxPortal>
          <ComboboxContent
            class="z-10 mt-1 min-w-48 w-full max-w-md bg-surface-modal overflow-hidden rounded-lg shadow-2xl ring-1 ring-black ring-opacity-5"
            position="popper"
            :align="'start'"
            @openAutoFocus.prevent
            @closeAutoFocus.prevent
          >
            <ComboboxViewport class="max-h-60 overflow-auto p-1.5">
              <ComboboxEmpty
                class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
              >
                <FeatherIcon v-if="fetchContacts" name="search" class="h-4" />
                {{ emptyStateText }}
              </ComboboxEmpty>
              <ComboboxItem
                v-for="option in options"
                :key="option.value"
                :value="option.value"
                class="text-base leading-none text-ink-gray-7 rounded flex items-center px-2 py-1 relative select-none data-[highlighted]:outline-none data-[highlighted]:bg-surface-gray-3 cursor-pointer"
                @mousedown.prevent="onSelect(option.value, option)"
              >
                <UserAvatar class="mr-2" :user="option.value" size="lg" />
                <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                  <div class="text-base font-medium">{{ option.label }}</div>
                  <div class="text-sm text-ink-gray-5">{{ option.value }}</div>
                </div>
              </ComboboxItem>
            </ComboboxViewport>
          </ComboboxContent>
        </ComboboxPortal>
      </ComboboxRoot>
    </div>

    <!-- Selected Attendees -->
    <div
      v-if="values.length"
      class="flex flex-col gap-2 mt-2 max-h-[165px] overflow-y-auto"
      ref="optionsRef"
    >
      <Button
        ref="emails"
        v-for="att in values"
        :key="att.email"
        :label="att.email"
        theme="gray"
        class="rounded-full w-fit"
        :tooltip="getTooltip(att.email)"
      >
        <template #prefix>
          <UserAvatar :user="att.email" class="-ml-1 !size-5.5" />
        </template>
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="removeValue(att.email)"
          />
        </template>
      </Button>
      <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
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
  validate: {
    type: Function,
    default: null,
  },
  variant: {
    type: String,
    default: 'subtle',
  },
  size: {
    type: String,
    default: 'sm',
  },
  placeholder: {
    type: String,
    default: 'Add attendee',
  },
  inputClass: {
    type: String,
    default: '',
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
  fetchContacts: {
    type: Boolean,
    default: true,
  },
  existingEmails: {
    type: Array,
    default: () => [],
  },
})

const values = defineModel()

const emails = ref([])
const search = ref(null)
const error = ref(null)
const info = ref(null)
const query = ref('')
const text = ref('')
const showOptions = ref(false)
const optionsRef = ref(null)
const tempSelection = ref(null)

const metaByEmail = computed(() => {
  const out = {}
  const source = values.value || []
  for (const a of source) {
    if (a?.email) out[a.email] = a
  }
  return out
})

function getTooltip(email) {
  const m = metaByEmail.value[email]
  if (!m) return email
  const parts = []
  if (m.reference_doctype) parts.push(m.reference_doctype)
  if (m.reference_docname) parts.push(m.reference_docname)
  return parts.length ? parts.join(': ') : email
}

watchDebounced(
  query,
  (val) => {
    val = val || ''
    if (text.value === val && options.value?.length) return
    text.value = val
    reload(val)
  },
  { debounce: 300, immediate: true },
)

const filterOptions = createResource({
  url: 'crm.api.contact.search_emails',
  method: 'POST',
  cache: [text.value, 'Contact'],
  params: { txt: text.value },
  transform: (data) => {
    let allData = data.map((option) => {
      let fullName = option[0]
      let email = option[1]
      let name = option[2]
      return {
        label: fullName || name || email,
        name: name,
        value: email,
      }
    })

    // Filter out existing emails
    if (props.existingEmails?.length) {
      allData = allData.filter((option) => {
        return !props.existingEmails.includes(option.value)
      })
    }

    return allData
  },
})

const options = computed(() => {
  let searchedContacts = props.fetchContacts ? filterOptions.data : []
  if (!searchedContacts?.length && query.value) {
    searchedContacts.push({
      name: 'new',
      label: query.value,
      value: query.value,
    })
  }
  return searchedContacts || []
})

const emptyStateText = computed(() =>
  props.fetchContacts
    ? __('No results found')
    : __('Type an email address to add attendee'),
)

function reload(val) {
  if (!props.fetchContacts) return

  filterOptions.update({
    params: { txt: val },
  })
  filterOptions.reload()
}

function onSelect(val, fullOption = null) {
  if (!val) return
  const optionObj = fullOption ||
    options.value.find((o) => o.value === val) || {
      name: 'new',
      label: val,
      value: val,
    }
  addValue(optionObj)
  if (!error.value) {
    query.value = ''
    tempSelection.value = null
    showOptions.value = false
    nextTick(() => setFocus())
  }
}

function handleEnter() {
  if (query.value) {
    onSelect(query.value, {
      name: 'new',
      label: query.value,
      value: query.value,
    })
  }
}

function onInput(e) {
  query.value = e.target.value
  showOptions.value = true
}

const addValue = (option) => {
  // Safeguard for falsy option
  if (!option || !option.value) return

  error.value = null
  info.value = null

  const current = Array.isArray(values.value) ? values.value.slice() : []
  const existing = new Set(current.map((a) => a.email))

  const raw = option.value || ''
  const parts = raw.split(',')
  const hasMultiple = parts.length > 1

  for (let p of parts) {
    p = p.trim()
    if (!p) continue
    if (existing.has(p)) {
      info.value = __('email already exists')
      continue
    }
    if (props.validate && !props.validate(p)) {
      error.value = props.errorMessage(p)
      query.value = p
      continue
    }
    existing.add(p)
    const entry = { email: p }

    if (option.name && !hasMultiple) {
      entry.reference_docname = option.name
    }
    current.push(entry)
  }

  values.value = current
  // Scroll to the bottom so the last added value is visible
  nextTick(() => {
    // use requestAnimationFrame to ensure DOM paint
    requestAnimationFrame(() => {
      const el = optionsRef.value
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
    })
  })
}

const removeValue = (email) => {
  values.value = (values.value || []).filter((a) => a.email !== email)
}

function setFocus() {
  search.value?.focus?.()
}

defineExpose({ setFocus })
</script>
