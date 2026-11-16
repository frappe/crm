<template>
  <div
    class="flex h-full w-full flex-col overflow-hidden rounded-4 border border-outline-gray-1 bg-surface-elevation-2"
  >
    <div class="flex shrink-0 items-start gap-2 pb-3 pl-4 pr-2 pt-4">
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <div class="flex h-6 min-w-0 items-center">
          <span class="truncate text-xl-semibold text-ink-gray-9">
            {{ title }}
          </span>
        </div>
        <slot name="subtitle">
          <div
            v-if="config && subtitleParts"
            class="flex min-w-0 items-center gap-1 text-base text-ink-gray-5"
          >
            <span v-if="subtitleParts[0]" class="shrink-0">
              {{ subtitleParts[0] }}
            </span>
            <PeriodPicker
              class="h-5 shrink-0 text-base"
              :period="doctype"
              :labels="RECORD_LABELS"
              @change="
                (value) => emit('update:config', { ...config, doctype: value })
              "
            />
            <span class="truncate">{{ subtitleParts[1] }}</span>
          </div>
          <span v-else class="truncate text-base text-ink-gray-5">
            {{ subtitle.replace('{0}', RECORD_LABELS[doctype]) }}
          </span>
        </slot>
      </div>
      <div v-if="$slots.tabs" class="shrink-0">
        <slot name="tabs" />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-2">
      <div v-if="loading" class="flex flex-1 items-center justify-center">
        <LoadingIndicator class="size-4 text-ink-gray-5" />
      </div>
      <HomeEmptyState
        v-else-if="!rows.length"
        class="flex-1 px-4 pb-10"
        :text="emptyText"
        :icon="emptyIcon"
      />
      <slot v-else :rows="rows" />
    </div>

    <div
      v-if="$slots.footer || (viewAll && total)"
      class="flex h-8 shrink-0 items-center justify-end px-2"
    >
      <slot name="footer" />
      <Button
        v-if="viewAll && total"
        variant="ghost"
        :label="__('View all')"
        iconRight="lucide-arrow-right"
        :route="viewAll"
      />
    </div>
  </div>
</template>
<script setup>
import HomeEmptyState from '@/components/Home/HomeEmptyState.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { RECORD_LABELS } from '@/utils/home'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  // With a config, {0} in the subtitle becomes the Lead, Deal or Both picker
  subtitle: { type: String, required: true },
  resource: { type: Object, required: true },
  config: { type: Object, default: null },
  viewAll: { type: Object, default: null },
  emptyText: { type: String, required: true },
  emptyIcon: { type: String, default: 'lucide-check-circle-2' },
})

const emit = defineEmits(['update:config'])

const doctype = computed(() => props.config?.doctype || 'Both')
const rows = computed(() => props.resource.data?.rows || [])
const total = computed(() => props.resource.data?.total || 0)
const loading = computed(() => props.resource.loading && !props.resource.data)

const subtitleParts = computed(() => {
  if (!props.subtitle.includes('{0}')) return null
  return props.subtitle.split('{0}').map((part) => part.trim())
})
</script>
