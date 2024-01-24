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
        class="rounded-full"
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
        <Combobox v-model="selectedValue" nullable>
          <Popover class="w-full" v-model:show="showOptions">
            <template #target="{ togglePopover }">
              <ComboboxInput
                ref="search"
                class="search-input form-input w-full border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
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
                @keydown.delete.capture.stop="removeLastValue"
              />
            </template>
            <template #body="{ isOpen }">
              <div v-show="isOpen">
                <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl">
                  <ComboboxOptions
                    class="my-1 max-h-[12rem] overflow-y-auto px-1.5"
                    static
                  >
                    <ComboboxOption
                      v-for="option in filterOptions"
                      :key="option.value"
                      :value="option"
                      v-slot="{ active }"
                    >
                      <li
                        :class="[
                          'flex cursor-pointer items-center rounded px-2 py-1 text-base',
                          { 'bg-gray-100': active },
                        ]"
                      >
                        <UserAvatar
                          class="mr-2"
                          :user="option.value"
                          size="lg"
                        />
                        <div class="flex flex-col gap-1 p-1 text-gray-800">
                          <div class="text-base font-medium">
                            {{ option.label }}
                          </div>
                          <div class="text-sm text-gray-600">
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
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
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
import { contactsStore } from '@/stores/contacts'
import { Popover } from 'frappe-ui'
import { ref, defineModel, computed, nextTick } from 'vue'

const props = defineProps({
  validate: {
    type: Function,
    default: null,
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
})

const values = defineModel()

const { getContacts } = contactsStore()

const emails = ref([])
const search = ref(null)
const error = ref(null)
const query = ref('')
const showOptions = ref(false)

const emailList = computed(() => {
  let contacts = getContacts() || []
  return (
    contacts
      ?.filter((contact) => contact.email_id)
      .map((contact) => {
        return {
          label: contact.full_name || contact.email_id,
          value: contact.email_id,
        }
      }) || []
  )
})

const selectedValue = computed({
  get: () => query.value || '',
  set: (val) => {
    query.value = ''
    if (val) {
      showOptions.value = false
    }
    addValue(val.value)
  },
})

const filterOptions = computed(() => {
  if (!query.value) {
    return emailList.value
  }
  let filteredList = emailList.value?.filter((option) => {
    let searchTexts = [option.label, option.value]
    return searchTexts.some((text) =>
      (text || '').toString().toLowerCase().includes(query.value.toLowerCase())
    )
  })

  if (filteredList.length === 0) {
    filteredList.push({
      label: query.value,
      value: query.value,
    })
  }

  return filteredList
})

const addValue = (value) => {
  error.value = null
  if (value) {
    const splitValues = value.split(',')
    splitValues.forEach((value) => {
      value = value.trim()
      if (value) {
        // check if value is not already in the values array
        if (!values.value.includes(value)) {
          // check if value is valid
          if (value && props.validate && !props.validate(value)) {
            error.value = props.errorMessage(value)
            return
          }
          // add value to values array
          values.value.push(value)
          value = value.replace(value, '')
        }
      }
    })
    !error.value && (value = '')
  }
}

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value)
}

const removeLastValue = () => {
  if (query.value) return

  let emailRef = emails.value[emails.value.length - 1].$el
  if (document.activeElement === emailRef) {
    values.value.pop()
    nextTick(() => {
      if (values.value.length) {
        emailRef = emails.value[emails.value.length - 1].$el
        emailRef.focus()
      } else {
        setFocus()
      }
    })
  } else {
    emailRef.focus()
  }
}

function setFocus() {
  search.value.$el.focus()
}

defineExpose({ setFocus })
</script>
