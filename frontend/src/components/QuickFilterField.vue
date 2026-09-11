<template>
  <FormControl
    v-if="filter.fieldtype == 'Check'"
    v-model="filter.value"
    :label="filter.label"
    type="checkbox"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <FormControl
    v-else-if="filter.fieldtype === 'Select'"
    v-model="filter.value"
    class="form-control cursor-pointer [&_select]:cursor-pointer"
    type="select"
    :options="filter.options"
    :placeholder="filter.label"
    @update:modelValue="updateFilter(filter, $event)"
  />
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
  />
  <component
    :is="filter.fieldtype === 'Date' ? DatePicker : DateTimePicker"
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="border-none"
    :value="filter.value"
    :placeholder="filter.label"
    :format="
      filter.fieldtype === 'Date'
        ? getFormat('', '', true, false, false)
        : getFormat('', '', true, true, false)
    "
    @change="(v) => updateFilter(filter, v)"
  />
  <FormControl
    v-else
    v-model="draft"
    type="text"
    :placeholder="filter.label"
    @focus="focused = true"
    @blur="focused = false"
    @input.stop="onTextInput($event.target.value)"
  />
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { FormControl, DatePicker, DateTimePicker } from 'frappe-ui'
import { getFormat } from '@/utils'
import { useDebounceFn } from '@vueuse/core'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  filter: { type: Object, required: true },
})

const filter = reactive(props.filter)

const emit = defineEmits(['applyQuickFilter'])

// Text filters are debounced, so between a keystroke and the list response the
// typed text is newer than `filter.value` — which the parent re-derives from
// the list's *applied* filters every time a response lands. Copying that back
// mid-edit wipes whatever was typed since the last commit (#2113), so the input
// owns a local draft and only follows the parent while the user isn't editing.
const draft = ref(props.filter.value ?? '')
const focused = ref(false)
const debouncePending = ref(false)
// Applies emitted to the parent that it hasn't reported back as settled yet.
const pendingApplies = ref(0)
const editing = computed(
  () => focused.value || debouncePending.value || pendingApplies.value > 0,
)

watch(
  () => props.filter,
  (newFilter) => {
    Object.assign(filter, newFilter)
    if (!editing.value) draft.value = newFilter.value ?? ''
  },
  { deep: true },
)

// The edit stays pending past blur, and past the debounce firing: applying a
// filter also saves the view and re-reads it, and an *earlier* apply finishing
// that round trip late rebuilds `filter.value` from a stale view. Until the
// parent reports every apply as settled, whatever the prop carries is older
// than the draft, so it's only re-synced once the last one has landed.
const debouncedFn = useDebounceFn((f, value) => {
  debouncePending.value = false
  pendingApplies.value++
  emit('applyQuickFilter', f, value, onApplySettled)
}, 500)

function onApplySettled() {
  pendingApplies.value--
  if (!editing.value) draft.value = props.filter.value ?? ''
}

function onTextInput(value) {
  debouncePending.value = true
  debouncedFn(filter, value)
}

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}
</script>
