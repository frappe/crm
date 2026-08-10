<template>
  <div class="fc-field">
    <!-- Read-only display -->
    <template v-if="isReadOnly">
      <label v-if="showLabel" class="block text-xs font-medium text-ink-gray-6 mb-1">{{ field.label }}</label>
      <div
        class="text-sm text-ink-gray-8 px-3 py-2 rounded-lg bg-surface-gray-2 border border-outline-gray-1 min-h-[36px] flex items-center"
        :class="isNumeric ? 'justify-end tabular-nums' : ''"
      >
        <template v-if="field.type === 'check'">{{ modelValue ? 'Yes' : 'No' }}</template>
        <template v-else-if="field.type === 'currency'">{{ formatCurrency(modelValue, currency) }}</template>
        <template v-else>{{ displayValue }}</template>
      </div>
    </template>

    <!-- Link -> Combobox (native server search) -->
    <div v-else-if="field.type === 'link'">
      <label v-if="showLabel" class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ field.label }}<span v-if="field.required" class="text-red-500 ml-0.5">*</span>
      </label>
      <Combobox
        :model-value="modelValue"
        :options="linkOptions"
        :filterable="false"
        :placeholder="'Search ' + (linkTarget || '') + '...'"
        @update:model-value="emitValue"
        @update:query="onLinkQuery"
      />
    </div>

    <!-- Date -> DatePicker -->
    <div v-else-if="field.type === 'date'">
      <label v-if="showLabel" class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ field.label }}<span v-if="field.required" class="text-red-500 ml-0.5">*</span>
      </label>
      <DatePicker
        :model-value="modelValue || ''"
        :placeholder="field.label"
        @update:model-value="emitValue"
      />
    </div>

    <!-- Currency: symbol prefix badge in edit mode -->
    <div v-else-if="field.type === 'currency'" :class="showLabel ? '' : ''">
      <label v-if="showLabel" class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ field.label }}<span v-if="field.required" class="text-red-500 ml-0.5">*</span>
      </label>
      <div class="flex items-center gap-1.5">
        <span v-if="currency" class="text-xs font-medium text-ink-gray-5 w-8 text-right flex-shrink-0">{{ currency }}</span>
        <FormControl
          type="number"
          :required="field.required"
          step="any"
          :model-value="modelValue ?? ''"
          class="fc-num flex-1"
          @update:model-value="emitNumber"
        />
      </div>
    </div>

    <!-- Number (int / float) -->
    <FormControl
      v-else-if="isNumeric"
      type="number"
      :label="showLabel ? field.label : undefined"
      :required="field.required"
      :step="numberStep"
      :model-value="modelValue ?? ''"
      class="fc-num"
      @update:model-value="emitNumber"
    />

    <!-- Select -->
    <FormControl
      v-else-if="field.type === 'select'"
      type="select"
      :label="showLabel ? field.label : undefined"
      :required="field.required"
      :options="selectOptions"
      :model-value="modelValue ?? ''"
      @update:model-value="emitValue"
    />

    <!-- Check -->
    <FormControl
      v-else-if="field.type === 'check'"
      type="checkbox"
      :label="field.label"
      :model-value="!!modelValue"
      @update:model-value="v => emitValue(v ? 1 : 0)"
    />

    <!-- Textarea -->
    <FormControl
      v-else-if="field.type === 'textarea'"
      type="textarea"
      :label="showLabel ? field.label : undefined"
      :required="field.required"
      :rows="3"
      :model-value="modelValue ?? ''"
      @update:model-value="emitValue"
    />

    <!-- Datetime -->
    <FormControl
      v-else-if="field.type === 'datetime'"
      type="datetime"
      :label="showLabel ? field.label : undefined"
      :required="field.required"
      :model-value="modelValue ?? ''"
      @update:model-value="emitValue"
    />

    <!-- Default: text -->
    <FormControl
      v-else
      type="text"
      :label="showLabel ? field.label : undefined"
      :required="field.required"
      :model-value="modelValue ?? ''"
      @update:model-value="emitValue"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { FormControl, Combobox, DatePicker, createResource, debounce } from 'frappe-ui'
import { useCurrency } from '../../composables/useCurrency.js'
import { isNumericType } from '../../constants/formLayouts.js'

const props = defineProps({
  // Normalized field object from formLayouts.js:
  // { fieldname, label, type, options, optionsField, required, readOnly, precision }
  field: { type: Object, required: true },
  modelValue: { default: null },
  showLabel: { type: Boolean, default: true },
  currency: { type: String, default: '' },
  forceReadOnly: { type: Boolean, default: false },
  // Effective link target doctype, resolved by the parent for Dynamic Links
  // (field.optionsField). Falls back to the field's static `options` otherwise.
  linkDoctype: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const { formatCurrency } = useCurrency()

const isReadOnly = computed(() => props.forceReadOnly || !!props.field.readOnly)
const isNumeric = computed(() => isNumericType(props.field.type))

const numberStep = computed(() => {
  if (props.field.type === 'int') return '1'
  const p = props.field.precision
  if (p) return String(1 / Math.pow(10, Number(p)))
  return 'any'
})

const displayValue = computed(() => {
  const v = props.modelValue
  return v === null || v === undefined || v === '' ? '—' : v
})

const selectOptions = computed(() => {
  const o = props.field.options
  if (Array.isArray(o)) return o
  return (o || '').split('\n')
})

function emitValue(v) {
  emit('update:modelValue', v)
}

function emitNumber(raw) {
  if (raw === '' || raw === null || raw === undefined) {
    emit('update:modelValue', null)
    return
  }
  const n = props.field.type === 'int' ? parseInt(raw, 10) : parseFloat(raw)
  emit('update:modelValue', Number.isNaN(n) ? null : n)
}

/* ---- Link (Combobox) native server search ---- */
const linkResults = ref([])
const linkResource = createResource({ url: 'frappe.client.get_list' })

// Effective target doctype: the parent-resolved linkDoctype (Dynamic Link)
// takes precedence; otherwise the field's static `options`.
const linkTarget = computed(() => props.linkDoctype || props.field.options || '')

// Keep the current value present as an option so its label renders even
// before a search populates the list.
const linkOptions = computed(() => {
  const opts = linkResults.value.slice()
  const v = props.modelValue
  if (v && !opts.some((o) => o.value === v)) opts.unshift({ label: v, value: v })
  return opts
})

// Monotonic request id: drop stale responses so a slower reply for an old
// target/query can't clobber results for the current one.
let linkReq = 0

const onLinkQuery = debounce(async (query) => {
  const target = linkTarget.value
  const req = ++linkReq
  if (!target) {
    linkResults.value = []
    return
  }
  try {
    const rows = await linkResource.submit({
      doctype: target,
      filters: query ? JSON.stringify([['name', 'like', `%${query}%`]]) : '[]',
      fields: JSON.stringify(['name']),
      limit_page_length: 10,
      order_by: 'modified desc',
    })
    if (req !== linkReq) return
    linkResults.value = (rows || []).map((r) => ({ label: r.name, value: r.name }))
  } catch {
    if (req === linkReq) linkResults.value = []
  }
}, 250)

// When the resolved target changes (e.g. quotation_to: Customer -> Lead), the
// prior results belong to the wrong doctype — clear and re-prefetch.
watch(linkTarget, () => {
  if (props.field.type !== 'link' || isReadOnly.value) return
  linkResults.value = []
  onLinkQuery('')
})

onMounted(() => {
  if (props.field.type === 'link' && !isReadOnly.value) onLinkQuery('')
})
</script>
