<template>
  <div class="-mx-[2px] space-y-1.5 px-[2px]">
    <label
      v-if="attrs.label"
      class="block"
      :class="labelClasses"
      :for="controlId"
    >
      {{ __(attrs.label) }}
      <template v-if="required">
        <span class="select-none text-ink-red-5" aria-hidden="true">*</span>
        <span class="sr-only">{{ __('(required)') }}</span>
      </template>
    </label>
    <Autocomplete
      ref="autocomplete"
      :button-id="controlId"
      v-model="value"
      :options="options.data"
      :size="attrs.size || 'sm'"
      :variant="props.variant"
      :placeholder="attrs.placeholder"
      :disabled="attrs.disabled"
      :placement="attrs.placement"
      :filterable="false"
    >
      <template #target="{ open, togglePopover }">
        <slot name="target" v-bind="{ open, togglePopover }" />
      </template>

      <template #prefix>
        <slot name="prefix" />
      </template>

      <template #item-prefix="{ active, selected, option }">
        <slot name="item-prefix" v-bind="{ active, selected, option }" />
      </template>

      <template #item-label="{ active, selected, option }">
        <slot name="item-label" v-bind="{ active, selected, option }">
          <div v-if="option.description" class="flex flex-col gap-1">
            <div class="flex-1 font-semibold truncate text-ink-gray-7">
              {{ option.label }}
            </div>
            <div class="flex-1 text-sm truncate text-ink-gray-5">
              {{ option.description }}
            </div>
          </div>
          <div v-else class="flex-1 truncate text-ink-gray-7">
            {{ option.label }}
          </div>
        </slot>
      </template>

      <template #footer="{ value: v, close }">
        <div v-if="attrs.onCreate">
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Create New')"
            iconLeft="lucide-plus"
            @click="() => attrs.onCreate(v, close)"
          />
        </div>
        <div>
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Clear')"
            iconLeft="lucide-x"
            @click="() => clearValue(close)"
          />
        </div>
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { isTranslatable } from '@/utils'
import { watchDebounced } from '@vueuse/core'
import { createResource } from 'frappe-ui'
import { useAttrs, computed, ref, useId } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  filters: { type: [Array, Object, String], default: () => [] },
  modelValue: { type: String, default: '' },
  hideMe: { type: Boolean, default: false },
  variant: { type: String, default: 'subtle' },
  required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const attrs = useAttrs()
const controlId = useId()

const valuePropPassed = computed(() => 'value' in attrs)
const selectedOption = ref(null)

const value = computed({
  get: () => {
    let v = valuePropPassed.value ? attrs.value : props.modelValue

    if (isTranslatable(props.doctype)) return __(v)
    return v
  },
  set: (val) => {
    if (!val?.value) return
    selectedOption.value = val
    emit(valuePropPassed.value ? 'change' : 'update:modelValue', val.value)
  },
})

const autocomplete = ref(null)
const text = ref('')

// Compared by content: callers often pass inline objects, which are new on
// every parent render and would otherwise force a reload each time.
const searchSource = computed(() =>
  JSON.stringify([props.doctype, props.filters]),
)

// One watcher, so a field sends one search when it mounts instead of one per
// watched value. A new doctype or filter always searches again; new text only
// searches if it differs from the last search.
watchDebounced(
  () => [autocomplete.value?.query || '', searchSource.value],
  ([query, source], [, previousSource] = []) => {
    text.value = query
    reload(query, source !== previousSource)
  },
  { debounce: 300, immediate: true },
)

const options = createResource({
  url: 'frappe.desk.search.search_link',
  cache: [props.doctype, text.value, props.hideMe, props.filters],
  // GET so the browser can reuse a search for the 60s the endpoint allows
  method: 'GET',
  params: searchParams(text.value, props.filters),
  transform: (data) => {
    let allData = data.map((option) => {
      return {
        label: option.label || option.value,
        value: option.value,
        description: stripHtml(option.description),
      }
    })
    retainSelectedOption(allData)
    if (!props.hideMe && props.doctype == 'User') {
      allData.unshift({
        label: '@me',
        value: '@me',
      })
    }
    return allData
  },
})

function stripHtml(html) {
  if (!html) return ''
  return html
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function retainSelectedOption(options) {
  const selected = selectedOption.value
  if (!selected || options.some((option) => option.value === selected.value))
    return
  options.unshift(selected)
}

function reload(val, force = false) {
  if (!props.doctype) return
  if (
    !force &&
    options.data?.length &&
    val === options.params?.txt &&
    props.doctype === options.params?.doctype
  )
    return

  options.update({ params: searchParams(val, props.filters) })
  options.reload()
}

// A GET request sends every param as text, so filters go as JSON; without
// this an object filter would arrive as "[object Object]".
function searchParams(txt, filters) {
  const params = { txt, doctype: props.doctype }
  if (filters) {
    params.filters =
      typeof filters === 'string' ? filters : JSON.stringify(filters)
  }
  return params
}

function clearValue(close) {
  selectedOption.value = null
  emit(valuePropPassed.value ? 'change' : 'update:modelValue', '')
  close()
}

const labelClasses = computed(() => {
  return [
    {
      sm: 'text-base',
      md: 'text-base',
    }[attrs.size || 'sm'],
    'text-ink-gray-5',
  ]
})

defineExpose({ reload })
</script>
