<template>
  <ItemListRow
    class="relative hover:bg-surface-gray-2 has-[a:focus-visible]:bg-surface-gray-3"
  >
    <template #prefix>
      <Tooltip :text="record.status">
        <span class="relative flex">
          <IndicatorIcon :class="statusColor" />
        </span>
      </Tooltip>
    </template>
    <RouterLink
      :to="recordRoute(record)"
      class="flex min-w-0 items-baseline gap-1.5 outline-none after:absolute after:inset-0"
    >
      <span class="truncate text-ink-gray-8">{{ label.title }}</span>
      <span v-if="label.subtitle" class="truncate text-ink-gray-5">
        {{ label.subtitle }}
      </span>
    </RouterLink>
    <template #suffix>
      <div class="relative flex items-center gap-2 text-ink-gray-5">
        <slot />
      </div>
    </template>
  </ItemListRow>
</template>
<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { statusesStore } from '@/stores/statuses'
import { recordRoute, recordTitle } from '@/utils/home'
import { ItemListRow, Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  record: { type: Object, required: true },
})

const { getLeadStatus, getDealStatus } = statusesStore()

const label = computed(() => recordTitle(props.record))

const statusColor = computed(() => {
  const getStatus =
    props.record.doctype === 'CRM Deal' ? getDealStatus : getLeadStatus
  return getStatus(props.record.status)?.color
})
</script>
