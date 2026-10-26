<template>
  <ListRow :class="homeRowClass">
    <ListCell>
      <Tooltip :text="record.status">
        <span class="relative flex">
          <IndicatorIcon :class="statusColor" />
        </span>
      </Tooltip>
    </ListCell>
    <ListCell class="gap-1.5">
      <RouterLink
        :to="recordRoute(record)"
        class="absolute inset-0 rounded-[10px]"
        :aria-label="label.title"
      />
      <span class="max-w-[70%] shrink-0 truncate text-ink-gray-8">
        {{ label.title }}
      </span>
      <span v-if="label.subtitle" class="truncate text-ink-gray-5">
        {{ label.subtitle }}
      </span>
    </ListCell>
    <slot />
  </ListRow>
</template>
<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { statusesStore } from '@/stores/statuses'
import { homeRowClass, recordRoute, recordTitle } from '@/utils/home'
import { Tooltip } from 'frappe-ui'
import { ListCell, ListRow } from 'frappe-ui/list'
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
