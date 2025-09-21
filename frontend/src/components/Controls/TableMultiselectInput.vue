<template>
  <div>
    <div
      class="group flex flex-wrap gap-1 min-h-20 p-1.5 rounded text-base bg-surface-gray-2 hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full"
    >
      <Button
        ref="valuesRef"
        v-for="value in parsedValues"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        class="rounded bg-surface-white hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4"
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
      <div class="w-full">
        <Link
          v-if="linkField"
          class="form-control flex-1 truncate cursor-text"
          :value="query"
          :filters="filters"
          :doctype="linkField.options"
          @change="(v) => addValue(v)"
          :hideMe="true"
        >
          <template #target="{ togglePopover }">
            <button
              class="w-full h-7 cursor-text"
              @click.stop="togglePopover"
            />
          </template>
        </Link>
      </div>
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { getMeta } from '@/stores/meta'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
})

const emit = defineEmits(['change'])

const { getFields } = getMeta(props.doctype)

const values = defineModel({
  type: Array,
  default: () => [],
})

const valuesRef = ref([])
const error = ref(null)
const query = ref('')

const linkField = ref('')

const filters = computed(() => {
  if (!linkField.value) return []
  return {
    name: ['not in', parsedValues.value],
  }
})

const parsedValues = computed(() => {
  error.value = ''
  getLinkField()
  if (!linkField.value) return []
  return values.value.map((row) => row[linkField.value.fieldname])
})

const getLinkField = () => {
  error.value = ''
  if (!linkField.value) {
    let fields = getFields()
    linkField.value = fields?.find((df) =>
      ['Link', 'User'].includes(df.fieldtype),
    )
    if (!linkField.value) {
      error.value =
        'Table MultiSelect requires a Table with atleast one Link field'
    }
  }
  return linkField.value
}

const addValue = (value) => {
  error.value = null

  if (values.value.some((row) => row[linkField.value.fieldname] === value)) {
    error.value = 'Value already exists'
    return
  }

  if (value) {
    values.value.push({ [linkField.value.fieldname]: value })
    emit('change', values.value)
    !error.value && (query.value = '')
  }
}

const removeValue = (value) => {
  let _value = values.value.filter(
    (row) => row[linkField.value.fieldname] !== value,
  )
  emit('change', _value)
}

const removeLastValue = () => {
  if (query.value) return

  let valueRef = valuesRef.value[valuesRef.value.length - 1]?.$el
  if (document.activeElement === valueRef) {
    values.value.pop()
    emit('change', values.value)
    nextTick(() => {
      if (values.value.length) {
        valueRef = valuesRef.value[valuesRef.value.length - 1].$el
        valueRef?.focus()
      }
    })
  } else {
    valueRef?.focus()
  }
}
</script>
