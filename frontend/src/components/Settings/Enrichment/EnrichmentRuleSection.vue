<template>
  <div class="flex flex-col">
    <div class="flex items-start justify-between gap-4 py-3">
      <div class="flex flex-col gap-1">
        <div class="text-lg-semibold text-ink-gray-8">{{ title }}</div>
        <div v-if="subtitle" class="text-p-sm text-ink-gray-6 max-w-lg">
          {{ subtitle }}
        </div>
      </div>
      <Button
        :label="addLabel"
        variant="subtle"
        icon-left="lucide-plus"
        @click="emit('add')"
      />
    </div>

    <div v-if="loading" class="flex items-center justify-center py-10">
      <LoadingIndicator class="size-6" />
    </div>
    <!-- Only stands in for the rows when there are none: a reload that fails
         after the first load keeps the rows up and toasts instead. -->
    <div
      v-else-if="error && !count"
      class="flex flex-col items-center justify-center gap-3 py-10"
    >
      <div class="text-p-base text-ink-gray-6 text-center">
        {{ error.messages?.[0] || errorMessage }}
      </div>
      <Button :label="__('Retry')" @click="emit('retry')" />
    </div>
    <div v-else-if="!count" class="h-40">
      <EmptyState
        :name="emptyName"
        :title="emptyTitle"
        :description="emptyDescription"
        :icon="emptyIcon"
        top="10%"
      />
    </div>
    <div v-else class="flex flex-col gap-3 py-2">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { Button, LoadingIndicator } from 'frappe-ui'
import EmptyState from '@/components/ListViews/EmptyState.vue'

// The frame every rule_type on the Rules tab shares: heading, "+ Add" button,
// and the one-of-four body (spinner / failed first load / nothing yet / rows).
// The rows themselves differ per rule_type and come in through the slot.
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  addLabel: { type: String, required: true },
  loading: { type: Boolean, default: false },
  error: { type: Object, default: null },
  errorMessage: { type: String, default: '' },
  count: { type: Number, default: 0 },
  emptyName: { type: String, required: true },
  emptyTitle: { type: String, default: '' },
  emptyDescription: { type: String, default: '' },
  emptyIcon: { type: String, default: 'file-text' },
})

const emit = defineEmits(['add', 'retry'])
</script>
