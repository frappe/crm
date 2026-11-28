<!-- frappe-ui's Select, or a bottom-sheet picker where phone pickers are on (see providePhonePickers). -->
<template>
  <SheetPicker v-if="usesSheet" v-bind="$attrs" :sheet-title="sheetTitle" />
  <Select v-else v-bind="$attrs">
    <template v-for="(_, name) in $slots" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps || {}" />
    </template>
  </Select>
</template>

<script setup>
import SheetPicker from '@/components/Controls/SheetPicker.vue'
import { usePhonePickers } from '@/composables/phone'
import { Select } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

defineProps({
  /** The phone sheet's heading, for a field whose label sits outside it. */
  sheetTitle: { type: String, default: '' },
})

const usesSheet = usePhonePickers()
</script>
