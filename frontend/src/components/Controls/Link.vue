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
        <span class="select-none text-ink-red-6" aria-hidden="true">*</span>
        <span class="sr-only">{{ __('(required)') }}</span>
      </template>
    </label>
    <Autocomplete
      ref="autocomplete"
      :button-id="controlId"
      v-model="value"
      :options="autocompleteOptions"
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
            iconLeft="plus"
            @click="() => attrs.onCreate(v, close)"
          />
        </div>
        <div>
          <Button
            variant="ghost"
            class="w-full !justify-start"
            :label="__('Clear')"
            iconLeft="x"
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
  /**
   * Split the dropdown into two labelled groups instead of filtering options
   * out: the ones matching `grouping.filters` first, everything else below.
   * `{ filters: { company_name: 'Frappe' }, label: '...', otherLabel: '...' }`
   * Only supported alongside object (or empty) `filters`.
   */
  grouping: { type: Object, default: null },
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

watchDebounced(
  () => autocomplete.value?.query,
  (val) => {
    val = val || ''
    if (text.value === val) return
    text.value = val
    reload(val)
  },
  { debounce: 300, immediate: true },
)

watchDebounced(
  () => props.doctype,
  () => reload(''),
  { debounce: 300, immediate: true },
)

watchDebounced(
  () => [props.filters, props.grouping],
  () => {
    reload('', true)
  },
  { debounce: 300, immediate: true },
)

// `filters` is only mergeable with `grouping.filters` when it is a plain
// object; an array or a JSON string is left alone and grouping is skipped.
function objectFilters() {
  const filters = props.filters
  if (Array.isArray(filters)) return filters.length ? null : {}
  if (typeof filters === 'string') return null
  return filters || {}
}

const isGrouped = computed(() =>
  Boolean(
    props.grouping?.filters &&
      props.grouping?.label &&
      props.grouping?.otherLabel &&
      objectFilters(),
  ),
)

function toOptions(data) {
  return data.map((option) => {
    return {
      label: option.label || option.value,
      value: option.value,
      description: stripHtml(option.description),
    }
  })
}

const options = createResource({
  url: 'frappe.desk.search.search_link',
  cache: [props.doctype, text.value, props.hideMe, props.filters],
  method: 'POST',
  params: {
    txt: text.value,
    doctype: props.doctype,
    filters: props.filters,
  },
  transform: (data) => {
    let allData = toOptions(data)
    // When grouped this resource only holds the second group, so retaining the
    // selection here would file it under the wrong label; see autocompleteOptions.
    if (isGrouped.value) return allData

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

// Holds the `grouping.filters` matches; `options` then holds everything else.
const groupedOptions = createResource({
  url: 'frappe.desk.search.search_link',
  cache: ['grouped', props.doctype, text.value, props.hideMe, props.filters],
  method: 'POST',
  params: {
    txt: text.value,
    doctype: props.doctype,
    filters: props.filters,
  },
  transform: toOptions,
})

const autocompleteOptions = computed(() => {
  if (!isGrouped.value) return options.data

  let matching = groupedOptions.data || []
  const others = options.data || []

  // retainSelectedOption's job for the grouped case: a selection that the
  // current search text filters out stays visible instead of looking cleared.
  // Neither group claims it, so it goes to the top of the first one.
  const selected = selectedOption.value
  if (
    selected &&
    !matching.some((option) => option.value === selected.value) &&
    !others.some((option) => option.value === selected.value)
  ) {
    matching = [selected, ...matching]
  }

  return [
    { group: props.grouping.label, items: matching },
    { group: props.grouping.otherLabel, items: others },
  ].filter((group) => group.items.length)
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

  if (!isGrouped.value) {
    options.update({
      params: {
        txt: val,
        doctype: props.doctype,
        filters: props.filters,
      },
    })
    options.reload()
    return
  }

  const baseFilters = objectFilters()
  const groupFilters = props.grouping.filters

  options.update({
    params: {
      txt: val,
      doctype: props.doctype,
      // `!=` is null-safe in frappe (it wraps the column in ifnull), so
      // records with the field unset land in this group rather than nowhere.
      filters: { ...baseFilters, ...negateFilters(groupFilters) },
    },
  })
  options.reload()

  groupedOptions.update({
    params: {
      txt: val,
      doctype: props.doctype,
      filters: { ...baseFilters, ...groupFilters },
    },
  })
  groupedOptions.reload()
}

function negateFilters(filters) {
  return Object.fromEntries(
    Object.entries(filters).map(([fieldname, value]) => [
      fieldname,
      ['!=', value],
    ]),
  )
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
