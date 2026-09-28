<template>
  <div class="flex flex-col gap-3" role="status">
    <div class="rounded-md p-3 text-base" :class="banner.class">
      {{ banner.message }}
    </div>
    <ul
      v-if="details.length"
      class="max-h-[240px] divide-y divide-outline-gray-1 overflow-y-auto rounded-md border border-outline-gray-2 text-sm"
    >
      <li
        v-for="(detail, i) in details"
        :key="i"
        class="flex gap-3 px-3 py-2 text-ink-gray-7"
      >
        <span v-if="detail.row" class="shrink-0 text-ink-gray-5">
          {{ __('Row {0}', [detail.row]) }}
        </span>
        <span>{{ detail.message }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { describeFailedRow, stripTags } from '@/utils/setup'
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, required: true },
})

const failedCount = computed(() => props.result.failedRows.length)

const banner = computed(() => {
  const { status, imported } = props.result
  if (status === 'Success') {
    return {
      class: 'bg-surface-green-2 text-ink-green-6',
      message: __('{0} leads imported.', [imported]),
    }
  }
  if (status === 'Partial Success') {
    return {
      class: 'bg-surface-amber-2 text-ink-amber-6',
      message: __('{0} leads imported, {1} rows failed.', [
        imported,
        failedCount.value,
      ]),
    }
  }
  return {
    class: 'bg-surface-red-2 text-ink-red-6',
    message: __(
      'The import did not go through. Fix the issues below and try again.',
    ),
  }
})

const details = computed(() => {
  const failed = props.result.failedRows.map(describeFailedRow)
  const warnings = (props.result.warnings || []).map((w) => ({
    row: w.row,
    message: stripTags(w.message),
  }))
  return [...failed, ...warnings]
})
</script>
