<template>
  <div class="h-full w-full">
    <!-- NUMBER KPI -->
    <div
      v-if="item.type === 'number_chart'"
      class="kpi-wrapper flex h-full w-full rounded-md overflow-hidden cursor-pointer shadow"
      :class="getKpiClass(item)"
    >
      <Tooltip :text="__(item?.data?.tooltip || '')" class="flex-1">
        <!-- Keep content transparent so the wrapper color shows through -->
        <div class="kpi-content w-full h-full p-3">
          <NumberChart v-if="item.data" :key="index" :config="item.data" class="w-full h-full" />
        </div>
      </Tooltip>
    </div>

    <!-- SPACER -->
    <div
      v-else-if="item.type === 'spacer'"
      class="rounded bg-surface-white h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>

    <!-- AXIS -->
    <div
      v-else-if="item.type === 'axis_chart'"
      class="h-full w-full rounded-md bg-surface-white shadow"
    >
      <AxisChart v-if="item.data" :config="item.data" />
    </div>

    <!-- DONUT -->
    <div
      v-else-if="item.type === 'donut_chart'"
      class="h-full w-full rounded-md bg-surface-white shadow overflow-hidden"
    >
      <DonutChart v-if="item.data" :config="item.data" />
    </div>
  </div>
</template>

<script setup>
import { AxisChart, DonutChart, NumberChart, Tooltip } from 'frappe-ui'

const props = defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})

/**
 * Backend can also send item.data.bgClass to override.
 */
const KPI_BG = {
  total_leads: 'bg-[#FFF7D3] text-black',                  // light yellow
  ongoing_deals: 'bg-[#FFDEC5] text-black',                // light orange
  won_deals: 'bg-[#B3E8F7] text-black',                    // light cyan
  average_won_deal_value: 'bg-[#D5F2ED] text-black',       // light teal
  average_deal_value: 'bg-[#BAE8E1] text-black',           // aqua
  average_time_to_close_a_lead: 'bg-[#DBD5FF] text-black', // lavender
  average_time_to_close_a_deal: 'bg-[#ECD3FF] text-black', // pastel violet (fixed)
  avg_call_duration: 'bg-[#FFD5F0] text-black',            // pink
}

function getKpiClass(item) {
  return item?.data?.bgClass || KPI_BG[item?.name] || 'bg-surface-white'
}
</script>

<style scoped>
/* Force inner cards from frappe-ui to be transparent inside colored KPIs */
.kpi-wrapper :deep(.bg-surface-white),
.kpi-wrapper :deep(.bg-white) {
  background-color: transparent !important;
}

/* Inherit text color from the wrapper */
.kpi-wrapper :deep([class*="text-ink-"]),
.kpi-wrapper :deep(.text-gray-500),
.kpi-wrapper :deep(.text-gray-700) {
  color: inherit !important;
}

/* Remove inner borders/shadows that clash with the color block */
.kpi-wrapper :deep(.shadow),
.kpi-wrapper :deep(.ring-1),
.kpi-wrapper :deep(.border) {
  box-shadow: none !important;
  border: 0 !important;
}
</style>
