<template>
  <div class="flex flex-col">
    <div class="flex items-start justify-between gap-4 py-3">
      <div class="text-lg-semibold text-ink-gray-8">{{ title }}</div>
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
    <!-- Only with no rows: a failed reload keeps the rows up and toasts. -->
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
      <!-- Widths match the row's so each label sits over its input. -->
      <div class="flex items-center gap-2 text-sm text-ink-gray-5">
        <div class="w-40 shrink-0">{{ columns[0] }}</div>
        <div class="flex-1 min-w-0">{{ columns[1] }}</div>
        <div class="w-8 shrink-0 whitespace-nowrap">{{ __('Enabled') }}</div>
        <div class="w-7 shrink-0" />
      </div>
      <slot />
      <div v-if="truncated" class="text-p-sm text-ink-gray-5">
        {{ __('Showing the first {0} rules', [RULE_LIMIT]) }}
      </div>
      <ErrorMessage
        v-for="(message, index) in errors"
        :key="index"
        :message="message"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, ErrorMessage, LoadingIndicator } from 'frappe-ui'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { RULE_LIMIT } from './useEnrichmentRules'

withDefaults(
  defineProps<{
    title: string
    addLabel: string
    // Labels for the two input columns, e.g. ['Platform', 'Pattern'].
    columns: string[]
    // Row errors (field checks and save failures), shown under the rows.
    errors?: string[]
    loading?: boolean
    error?: { messages?: string[] } | null
    errorMessage?: string
    count?: number
    emptyName: string
    emptyTitle?: string
    emptyDescription?: string
    emptyIcon?: string
    truncated?: boolean
  }>(),
  {
    errors: () => [],
    loading: false,
    error: null,
    errorMessage: '',
    count: 0,
    emptyTitle: '',
    emptyDescription: '',
    emptyIcon: 'file-text',
    truncated: false,
  },
)

const emit = defineEmits<{
  add: []
  retry: []
}>()
</script>
