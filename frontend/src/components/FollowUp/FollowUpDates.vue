<template>
  <div class="flex flex-col">
    <ItemListRow
      v-for="preset in presets"
      :key="preset.key"
      as="button"
      type="button"
      :class="rowClass"
      :disabled="disabled"
      @click="select(preset.date)"
    >
      {{ preset.label }}
      <template #suffix>
        <span class="text-ink-gray-5">{{ formatDay(preset.date) }}</span>
      </template>
    </ItemListRow>
    <DatePicker
      :model-value="''"
      :min="presets[0].date"
      @update:modelValue="select"
    >
      <template #trigger="{ setOpen }">
        <ItemListRow
          as="button"
          type="button"
          :class="rowClass"
          :disabled="disabled"
          @click="setOpen(true)"
        >
          {{ __('Pick date…') }}
        </ItemListRow>
      </template>
    </DatePicker>
  </div>
</template>
<script setup>
import { followUpPresets } from '@/utils/task'
import { DatePicker, ItemListRow, dayjs } from 'frappe-ui'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

const rowClass =
  'text-left outline-none hover:bg-surface-gray-3 focus-visible:bg-surface-gray-3'

const presets = followUpPresets()

function select(date) {
  if (date && !props.disabled) emit('select', date)
}

function formatDay(date) {
  return dayjs(date).format('ddd, D MMM')
}
</script>
