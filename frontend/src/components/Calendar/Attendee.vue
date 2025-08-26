<template>
  <div>
    <div
      class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7 [&>div]:w-full"
    >
      <Combobox v-model="selectedValue" nullable class="w-full">
        <Popover v-model:show="showOptions">
          <template #target="{ togglePopover }">
            <TextInput
              ref="search"
              type="text"
              size="md"
              class="w-full"
              variant="outline"
              v-model="query"
              :debounce="300"
              :placeholder="placeholder"
              @click="togglePopover"
              @keydown.delete.capture.stop="removeLastValue"
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
                <ComboboxOptions
                  class="p-1.5 max-h-[12rem] overflow-y-auto"
                  static
                >
                  <div
                    v-if="!options.length"
                    class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                  >
                    <FeatherIcon
                      v-if="fetchContacts"
                      name="search"
                      class="h-4"
                    />
                    {{
                      fetchContacts
                        ? __('No results found')
                        : __('Type an email address to add attendee')
                    }}
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
                  </ComboboxOption>
                </ComboboxOptions>
              </div>
            </div>
          </template>
        </Popover>
      </Combobox>
    </div>
    <div v-if="values.length" class="flex flex-col gap-2 px-4.5 py-[7px]">
      <Button
        ref="emails"
        v-for="att in values"
        :key="att.email"
        :label="att.email"
        theme="gray"
        class="rounded-full w-fit"
        :tooltip="getTooltip(att.email)"
        @keydown.delete.capture.stop="removeLastValue"
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
import { Combobox, ComboboxOptions, ComboboxOption } from '@headlessui/vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Popover from '@/components/frappe-ui/Popover.vue'
import { createResource, TextInput } from 'frappe-ui'
import { ref, computed, nextTick } from 'vue'
import { watchDebounced } from '@vueuse/core'
import FeatherIcon from 'frappe-ui/src/components/FeatherIcon.vue'

const props = defineProps({
  validate: {
    type: Function,
    default: null,
  },
  variant: {
    type: String,
    default: 'subtle',
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

const selectedValue = computed({
  get: () => query.value || '',
  set: (val) => {
    query.value = ''
    if (val) {
      showOptions.value = false
    }
    addValue(val)
  },
})

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

  if (!error.value) {
    values.value = current
  }
}

const removeValue = (email) => {
  values.value = (values.value || []).filter((a) => a.email !== email)
}

const removeLastValue = () => {
  if (query.value) return

  let emailRef = emails.value[emails.value.length - 1]?.$el
  if (document.activeElement === emailRef) {
    values.value.pop()
    nextTick(() => {
      if (values.value.length) {
        emailRef = emails.value[emails.value.length - 1].$el
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
  search.value.$el.focus()
}

defineExpose({ setFocus })
</script>
