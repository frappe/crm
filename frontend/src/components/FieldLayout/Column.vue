<template>
  <div class="column flex flex-col gap-4 min-w-0 flex-1">
    <div
      v-if="column.label && !column.hideLabel"
      class="text-ink-gray-9 max-w-fit text-base"
    >
      {{ column.label }}
    </div>
    <template v-for="field in fields" :key="field.fieldname">
      <Field :field="field" :data-name="field.fieldname" />
    </template>
  </div>
</template>
<script setup>
import Field from '@/components/FieldLayout/Field.vue'
import { computed } from 'vue'

const props = defineProps({
  column: { type: Object, required: true },
})

// skip entries that are not resolved field objects (e.g. a fieldname whose
// field was deleted after the layout was saved)
const fields = computed(() =>
  (props.column.fields || []).filter(
    (field) => field && typeof field === 'object' && field.fieldname,
  ),
)
</script>
