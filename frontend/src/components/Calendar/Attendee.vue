<template>
  <div>
    <div
      class="flex items-center justify-between text-ink-gray-7 [&>div]:w-full"
    >
      <Popover v-model:show="showOptions">
        <template #target="{ togglePopover }">
          <TextInput
            ref="search"
            type="text"
            :size="size"
            class="w-full"
            variant="outline"
            v-model="query"
            :debounce="300"
            :placeholder="placeholder"
            @click="togglePopover"
            @keydown="onKeydown"
          >
            <template #suffix>
              <FeatherIcon
                name="chevron-down"
                class="h-4 text-ink-gray-5"
                @click.stop="togglePopover()"
              />
            </template>
          </TextInput>
        </template>
        <template #body="{ isOpen }">
          <div v-show="isOpen">
            <div
              class="mt-1 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
            >
              <ul
                v-if="options.length"
                role="listbox"
                class="p-1.5 max-h-[12rem] overflow-y-auto"
              >
                <li
                  v-for="(option, idx) in options"
                  :key="option.value"
                  role="option"
                  :aria-selected="idx === highlightIndex"
                  @click="selectOption(option)"
                  @mouseenter="highlightIndex = idx"
                  class="flex cursor-pointer items-center rounded px-2 py-1 text-base"
                  :class="{ 'bg-surface-gray-3': idx === highlightIndex }"
                >
                  <UserAvatar class="mr-2" :user="option.value" size="lg" />
                  <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                    <div class="text-base font-medium">
                      {{ option.label }}
                    </div>
                    <div class="text-sm text-ink-gray-5">
                      {{ option.value }}
                    </div>
                  </div>
                </li>
              </ul>
              <div
                v-else
                class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
              >
                <FeatherIcon v-if="fetchContacts" name="search" class="h-4" />
                {{
                  fetchContacts
                    ? __('No results found')
                    : __('Type an email address to add attendee')
                }}
              </div>
            </div>
          </div>
        </template>
      </Popover>
    </div>
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
import { createResource, TextInput, Popover } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'
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
const highlightIndex = ref(-1)

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

function reload(val) {
  if (!props.fetchContacts) return

  filterOptions.update({
    params: { txt: val },
  })
  filterOptions.reload()
}

watch(
  () => options.value,
  () => {
    highlightIndex.value = options.value.length ? 0 : -1
  },
)

function selectOption(option) {
  if (!option) return
  addValue(option)
  !error.value && (query.value = '')
  showOptions.value = false
}

function onKeydown(e) {
  if (e.key === 'Enter') {
    if (highlightIndex.value >= 0 && options.value[highlightIndex.value]) {
      selectOption(options.value[highlightIndex.value])
    } else if (query.value) {
      // Add entered email directly
      selectOption({ name: 'new', label: query.value, value: query.value })
    }
    e.preventDefault()
  } else if (e.key === 'Escape') {
    showOptions.value = false
  }
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
  search.value.$el.focus()
}

defineExpose({ setFocus })
</script>
