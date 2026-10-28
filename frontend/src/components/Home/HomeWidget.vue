<template>
  <div
    class="flex h-full w-full flex-col overflow-hidden rounded-4 border border-outline-gray-1 bg-surface-elevation-2"
  >
    <div
      class="flex shrink-0 items-start gap-2 pb-3 pl-4 pt-4"
      :class="editing ? 'pr-16' : 'pr-2'"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <div class="flex h-6 min-w-0 items-center gap-1.5">
          <span class="truncate text-xl-semibold text-ink-gray-9">
            {{ title }}
          </span>
          <Dropdown v-if="config" :options="doctypeOptions">
            <Button
              variant="ghost"
              size="sm"
              :label="doctypeLabels[doctype]"
              iconRight="lucide-chevron-down"
            />
          </Dropdown>
        </div>
        <span class="truncate text-base text-ink-gray-5">{{ subtitle }}</span>
      </div>
      <div v-if="$slots.tabs" class="shrink-0">
        <slot name="tabs" />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-2">
      <div v-if="loading" class="flex flex-1 items-center justify-center">
        <LoadingIndicator class="size-4 text-ink-gray-5" />
      </div>
      <div
        v-else-if="!rows.length"
        class="flex flex-1 flex-col items-center justify-center gap-3 px-4 pb-10 text-center"
      >
        <span
          class="flex size-8 items-center justify-center rounded-full bg-surface-gray-2"
        >
          <span :class="emptyIcon" class="size-4 text-ink-gray-5" />
        </span>
        <span class="max-w-64 text-p-base text-ink-gray-6">
          {{ emptyText }}
        </span>
      </div>
      <slot v-else :rows="rows" />
    </div>

    <div
      v-if="viewAll && total"
      class="flex h-8 shrink-0 items-center justify-end px-2"
    >
      <Button
        variant="ghost"
        :label="__('View all')"
        iconRight="lucide-arrow-right"
        :route="viewAll"
      />
    </div>
  </div>
</template>
<script setup>
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { Dropdown } from 'frappe-ui'
import { computed, inject, ref } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  resource: { type: Object, required: true },
  config: { type: Object, default: null },
  viewAll: { type: Object, default: null },
  emptyText: { type: String, required: true },
  emptyIcon: { type: String, default: 'lucide-check-circle-2' },
})

const emit = defineEmits(['update:config'])

const editing = inject('homeEditing', ref(false))

const doctypeLabels = {
  Both: __('All'),
  Lead: __('Leads'),
  Deal: __('Deals'),
}

const doctype = computed(() => props.config?.doctype || 'Both')
const rows = computed(() => props.resource.data?.rows || [])
const total = computed(() => props.resource.data?.total || 0)
const loading = computed(() => props.resource.loading && !props.resource.data)

const doctypeOptions = computed(() => [
  {
    group: __('Show'),
    options: Object.entries(doctypeLabels).map(([value, label]) => ({
      label,
      selected: value === doctype.value,
      onClick: () => {
        if (value !== doctype.value) emit('update:config', { doctype: value })
      },
    })),
  },
])
</script>
