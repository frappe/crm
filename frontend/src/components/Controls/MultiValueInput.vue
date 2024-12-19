<template>
  <div>
    <div
      class="group flex flex-wrap gap-1 min-h-20 p-1.5 cursor-text rounded h-7 text-base bg-surface-gray-2 hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full"
      @click="setFocus"
    >
      <Button
        ref="emails"
        v-for="value in values"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        class="rounded bg-surface-gray-3 group-hover:bg-surface-gray-4 focus-visible:ring-outline-gray-4"
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
        <input
          ref="search"
          class="w-full border-none h-7 text-base bg-surface-gray-2 group-hover:bg-surface-gray-3 focus:border-none focus:!shadow-none focus-visible:!ring-0 transition-colors"
          type="text"
          v-model="query"
          placeholder="example@email.com"
          @keydown.enter.capture.stop="addValue()"
          @keydown.delete.capture.stop="removeLastValue"
        />
      </div>
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import { TextInput } from 'frappe-ui'
import { ref, nextTick } from 'vue'

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

const emails = ref([])
const search = ref(null)
const error = ref(null)
const query = ref('')

const addValue = () => {
  let value = query.value
  error.value = null
  if (value) {
    const splitValues = value.split(',')
    splitValues.forEach((value) => {
      value = value.trim()
      if (value) {
        // check if value is not already in the values array
        if (!values.value?.includes(value)) {
          // check if value is valid
          if (value && props.validate && !props.validate(value)) {
            error.value = props.errorMessage(value)
            return
          }
          // add value to values array
          if (!values.value) {
            values.value = [value]
          } else {
            values.value.push(value)
          }
          value = value.replace(value, '')
        }
      }
    })
    !error.value && (query.value = '')
  }
}

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value)
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
  search.value.focus()
}

defineExpose({ setFocus })
</script>
