<template>
  <div
    class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-2.5"
  >
    <span class="text-lg font-medium text-ink-gray-9">{{ title }}</span>
    <Button variant="solid" icon-left="lucide-plus" :label="__('Create')" />
  </div>
  <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-2">
    <Button icon-left="lucide-list-filter" :label="__('Filter')" />
    <Button icon-left="lucide-arrow-up-down" :label="__('Sort')" />
    <Button icon-left="lucide-columns-3" :label="__('Columns')" />
  </div>
  <div
    class="grid grid-cols-[16px_1.6fr_1fr_auto] items-center gap-3 border-b border-outline-gray-1 px-4 py-2 text-sm text-ink-gray-5"
  >
    <Checkbox :model-value="false" />
    <span>{{ __('Name') }}</span>
    <span>{{ __('Status') }}</span>
    <span class="w-12 text-right">{{ lastLabel }}</span>
  </div>
  <div
    v-for="(row, i) in rows"
    :key="row.name"
    class="preview-row grid grid-cols-[16px_1.6fr_1fr_auto] items-center gap-3 border-b border-outline-gray-1 px-4 py-2 text-base"
    :style="{ animationDelay: `${i * stagger}ms` }"
  >
    <Checkbox :model-value="false" />
    <span class="flex min-w-0 items-center gap-2 text-ink-gray-9">
      <Avatar :label="row.name" size="sm" />
      <span class="truncate">{{ row.name }}</span>
    </span>
    <span class="flex items-center gap-1.5 text-ink-gray-7">
      <IndicatorIcon :class="STATUS_COLORS[row.status]" />
      {{ __(row.status) }}
    </span>
    <span class="w-12 text-right">
      <Avatar v-if="row.owner" :label="row.owner" size="sm" class="ml-auto" />
      <span v-else class="text-sm tabular-nums text-ink-gray-5">
        {{ row.when }}
      </span>
    </span>
  </div>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { Avatar, Button, Checkbox } from 'frappe-ui'

defineProps({
  title: { type: String, required: true },
  rows: { type: Array, required: true },
  stagger: { type: Number, default: 40 },
  lastLabel: { type: String, default: __('Modified') },
})

const STATUS_COLORS = {
  New: 'text-ink-gray-5',
  Contacted: 'text-ink-amber-5',
  Nurture: 'text-ink-blue-5',
  Qualified: 'text-ink-green-5',
}
</script>

<style scoped>
.preview-row {
  animation: preview-fade-up 260ms ease-out both;
}

@keyframes preview-fade-up {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .preview-row {
    animation: none;
  }
}
</style>
