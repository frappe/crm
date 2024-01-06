<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        v-for="value in values"
        :label="value"
        theme="gray"
        variant="subtle"
        class="rounded-full"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="removeValue(value)"
          />
        </template>
      </Button>
      <TextInput
        class="min-w-20 flex-1 border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
        v-model="currentValue"
        @keydown.enter.capture.stop="addValue"
        @keydown.tab.capture.stop="addValue"
        @keydown.delete.capture.stop="removeLastValue"
        @keydown.meta.delete.capture.stop="removeAllValue"
      />
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import { ref, defineModel } from 'vue'

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
const currentValue = ref('')
const error = ref(null)

const addValue = () => {
  error.value = null
  if (currentValue.value) {
    const splitValues = currentValue.value.split(',')
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
          currentValue.value = currentValue.value.replace(value, '')
        }
      }
    })
    !error.value && (currentValue.value = '')
  }
}

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value)
}

const removeAllValue = () => {
  values.value = []
}

const removeLastValue = () => {
  if (!currentValue.value) {
    values.value.pop()
  }
}
</script>
