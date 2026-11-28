<!-- A Select or Link field on a phone: the value and a chevron, which open a bottom sheet to pick from. -->
<template>
  <div class="flex w-full flex-col gap-1.5">
    <label v-if="label" :for="controlId" class="text-xs text-ink-gray-5">
      {{ label }}
      <span v-if="required" class="text-ink-red-4" aria-hidden="true">*</span>
    </label>
    <slot name="target" :open="open" :toggle-popover="toggle">
      <button
        :id="controlId"
        type="button"
        class="flex h-7 w-full items-center gap-2 rounded-4 bg-surface-gray-2 px-2 text-left text-base hover:bg-surface-gray-3 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="disabled"
        :aria-haspopup="'dialog'"
        :aria-expanded="open"
        @click="open = true"
      >
        <slot name="prefix" />
        <span
          class="min-w-0 flex-1 truncate"
          :class="display ? 'text-ink-gray-8' : 'text-ink-gray-4'"
        >
          {{ display || placeholder || __('Select') }}
        </span>
        <span
          class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
      </button>
    </slot>
    <p v-if="description" class="text-p-sm text-ink-gray-5">
      {{ description }}
    </p>

    <BottomSheet
      v-model:open="open"
      :title="sheetTitle || label || placeholder"
    >
      <div class="flex flex-col px-2 pb-8">
        <div v-if="isLink || selectOptions.length > 12" class="px-2 pb-2">
          <TextInput
            v-model="query"
            type="search"
            :placeholder="__('Search')"
            :aria-label="__('Search')"
          >
            <template #prefix>
              <span
                class="lucide-search size-4 text-ink-gray-5"
                aria-hidden="true"
              />
            </template>
          </TextInput>
        </div>
        <button
          v-for="option in shownOptions"
          :key="option.value"
          type="button"
          class="flex items-center gap-3 rounded-4 px-3 py-2.5 text-start hover:bg-surface-gray-2"
          :aria-pressed="option.value === modelValue"
          @click="choose(option.value)"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="truncate text-p-base text-ink-gray-8">
              {{ option.label }}
            </span>
            <span
              v-if="option.description"
              class="truncate text-sm text-ink-gray-5"
            >
              {{ option.description }}
            </span>
          </span>
          <span
            v-if="option.value === modelValue"
            class="lucide-check size-4 shrink-0 text-ink-gray-7"
            aria-hidden="true"
          />
        </button>
        <p
          v-if="!shownOptions.length && !search.loading"
          class="px-3 py-6 text-center text-sm text-ink-gray-5"
        >
          {{ query ? __('No results for "{0}"', [query]) : __('No options') }}
        </p>
        <button
          v-if="canCreate"
          type="button"
          class="mt-1 flex items-center gap-2 border-t border-outline-gray-1 px-3 py-2.5 text-start text-p-base text-ink-gray-8 hover:bg-surface-gray-2"
          @click="emit('create', query, () => (open = false))"
        >
          <span class="lucide-plus size-4" aria-hidden="true" />
          {{ __('Create New') }}
        </button>
        <button
          v-if="canClear"
          type="button"
          class="mt-1 border-t border-outline-gray-1 px-3 py-2.5 text-start text-p-base text-ink-gray-6 hover:bg-surface-gray-2"
          @click="choose('')"
        >
          {{ __('Clear') }}
        </button>
      </div>
    </BottomSheet>
  </div>
</template>

<script setup>
import { useBackClose } from '@/composables/phone'
import { watchDebounced } from '@vueuse/core'
import { BottomSheet, TextInput, createResource } from 'frappe-ui'
import { computed, ref, useId, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  description: { type: String, default: '' },
  /** The sheet's heading, for a field whose label sits outside it. */
  sheetTitle: { type: String, default: '' },
  /** Select: strings or `{ label, value }`. Leave out for a Link. */
  options: { type: Array, default: null },
  /** Link: the doctype to search. */
  doctype: { type: String, default: '' },
  filters: { type: [Array, Object, String], default: () => [] },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  /** Link: offer Create New, which emits `create(query, close)`. */
  canCreate: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'create'])

const controlId = useId()
const open = ref(false)
const query = ref('')
const isLink = computed(() => !props.options)

useBackClose(
  () => open.value,
  () => (open.value = false),
)

const selectOptions = computed(() =>
  (props.options || []).map((option) =>
    typeof option === 'object'
      ? {
          label: option.label ?? option.value,
          value: option.value,
          description: option.description,
        }
      : { label: String(option), value: option },
  ),
)

const search = createResource({
  url: 'frappe.desk.search.search_link',
  method: 'GET',
  transform: (results) =>
    results.map((result) => ({
      label: result.label || result.value,
      value: result.value,
      description: stripHtml(result.description),
    })),
})

watch(open, (isOpen) => {
  if (!isOpen) return
  query.value = ''
  if (isLink.value) runSearch('')
})

watchDebounced(query, (text) => open.value && isLink.value && runSearch(text), {
  debounce: 300,
})

function runSearch(text) {
  const filters = props.filters
  search.submit({
    txt: text,
    doctype: props.doctype,
    filters: typeof filters === 'string' ? filters : JSON.stringify(filters),
  })
}

const shownOptions = computed(() => {
  if (isLink.value) return search.data || []
  const text = query.value.toLowerCase()
  // an empty option is offered as Clear, below the list
  return selectOptions.value.filter(
    (option) =>
      option.value !== '' && String(option.label).toLowerCase().includes(text),
  )
})

// a Select clears only to an empty option it offers
const canClear = computed(() => {
  if (!props.modelValue || props.required) return false
  return (
    isLink.value || selectOptions.value.some((option) => option.value === '')
  )
})

const display = computed(() => {
  if (!props.modelValue) return ''
  const option = selectOptions.value.find(
    (option) => option.value == props.modelValue,
  )
  return option?.label ?? props.modelValue
})

function choose(value) {
  emit('update:modelValue', value)
  open.value = false
}

function toggle() {
  open.value = !open.value
}

function stripHtml(html) {
  return (html || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
</script>
