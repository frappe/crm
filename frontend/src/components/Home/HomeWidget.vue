<template>
  <div
    class="flex h-full w-full flex-col overflow-hidden rounded-4 border border-outline-gray-1 bg-surface-elevation-2"
  >
    <div class="flex h-11 shrink-0 items-center gap-1.5 pl-4 pr-2">
      <span class="truncate text-base-medium text-ink-gray-8">
        {{ title }}
      </span>
      <span v-if="total" class="text-base tabular-nums text-ink-gray-5">
        {{ total }}
      </span>
      <div v-if="config" class="ml-auto">
        <Dropdown :options="doctypeOptions" align="end">
          <Button
            variant="ghost"
            :label="doctypeLabels[doctype]"
            iconRight="lucide-chevron-down"
          />
        </Dropdown>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-2">
      <div v-if="loading" class="flex flex-1 items-center justify-center">
        <LoadingIndicator class="size-4 text-ink-gray-5" />
      </div>
      <div
        v-else-if="!rows.length"
        class="flex flex-1 flex-col items-center justify-center gap-2 px-4 pb-4 text-center"
      >
        <span :class="emptyIcon" class="size-5 text-ink-gray-4" />
        <span class="text-p-base text-ink-gray-6">{{ emptyText }}</span>
      </div>
      <div v-else class="flex flex-col">
        <slot :rows="rows" />
      </div>
    </div>

    <div v-if="viewAll.length && total" class="flex shrink-0 justify-end p-2">
      <Button
        v-if="viewAll.length === 1"
        variant="ghost"
        :label="__('View all')"
        iconRight="lucide-arrow-right"
        :route="viewAll[0].route"
      />
      <Dropdown v-else :options="viewAll" align="end">
        <Button
          variant="ghost"
          :label="__('View all')"
          iconRight="lucide-chevron-down"
        />
      </Dropdown>
    </div>
  </div>
</template>
<script setup>
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  // a get_widget resource, or plain `{ data: { rows, total } }`
  resource: { type: Object, required: true },
  // leave unset for widgets without the Lead | Deal | Both setting
  config: { type: Object, default: null },
  // `{ label, route }` per list view; more than one shows a menu
  viewAll: { type: Array, default: () => [] },
  emptyText: { type: String, required: true },
  emptyIcon: { type: String, default: 'lucide-check-circle-2' },
})

const emit = defineEmits(['update:config'])

const doctypeLabels = {
  Both: __('Leads & deals'),
  Lead: __('Leads'),
  Deal: __('Deals'),
}

const doctype = computed(() => props.config?.doctype || 'Both')
const rows = computed(() => props.resource.data?.rows || [])
const total = computed(() => props.resource.data?.total || 0)
const loading = computed(() => props.resource.loading && !props.resource.data)

const doctypeOptions = computed(() =>
  Object.entries(doctypeLabels).map(([value, label]) => ({
    label,
    selected: value === doctype.value,
    onClick: () => {
      if (value !== doctype.value) emit('update:config', { doctype: value })
    },
  })),
)
</script>
