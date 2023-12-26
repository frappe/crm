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
        class="min-w-20 flex-1 border-none bg-white hover:bg-white focus:border-none focus:shadow-none focus-visible:ring-0"
        v-model="currentValue"
        @keydown.enter.capture.stop="addValue"
        @keydown.delete.capture.stop="removeLastValue"
      />
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import { Button, ErrorMessage, FeatherIcon, TextInput } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  values: {
    type: Array,
    default: () => [],
  },
  validate: {
    type: Function,
    default: null,
  },
  errorMessage: {
    type: String,
    default: 'Invalid value',
  },
})

const currentValue = ref('')
const values = ref(props.values)
const error = ref(null)

const addValue = () => {
  error.value = null
  if (
    currentValue.value &&
    props.validate &&
    !props.validate(currentValue.value)
  ) {
    error.value = props.errorMessage
    return
  }
  if (currentValue.value) {
    values.value.push(currentValue.value)
    currentValue.value = ''
  }
}

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value)
}

const removeLastValue = () => {
  if (!currentValue.value) {
    values.value.pop()
  }
}
</script>
