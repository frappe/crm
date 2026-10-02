<template>
  <div class="h-full w-full">
    <div
      v-if="item.type == 'number_chart'"
      class="flex h-full w-full overflow-hidden cursor-pointer"
    >
      <Tooltip :text="__(item.data.tooltip)">
        <NumberCard
          v-if="item.data"
          :key="index"
          class="h-full"
          v-bind="numberCardProps"
        />
      </Tooltip>
    </div>
    <div
      v-else-if="item.type == 'spacer'"
      class="rounded-4 bg-surface-base h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>
    <ChartCard v-else-if="item.type == 'axis_chart'" class="h-full">
      <component
        :is="axisChart.component"
        v-if="item.data"
        v-bind="axisChart.props"
      />
    </ChartCard>
    <ChartCard v-else-if="item.type == 'donut_chart'" class="h-full">
      <DonutChart v-if="item.data" v-bind="donutChartProps" />
    </ChartCard>
  </div>
</template>
<script setup>
import { Tooltip } from 'frappe-ui'
import {
  AreaChart,
  BarChart,
  ChartCard,
  DonutChart,
  LineChart,
  NumberCard,
} from 'frappe-ui/charts'
import {
  getAxisChartKind,
  toAxisChartProps,
  toDonutChartProps,
  toNumberCardProps,
} from '@/utils/dashboardCharts'
import { computed } from 'vue'

const props = defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})

const axisChartComponents = { line: LineChart, area: AreaChart, bar: BarChart }

const config = computed(() => props.item.data || {})

const numberCardProps = computed(() => toNumberCardProps(config.value))
const donutChartProps = computed(() => toDonutChartProps(config.value))
const axisChart = computed(() => ({
  component: axisChartComponents[getAxisChartKind(config.value)],
  props: toAxisChartProps(config.value),
}))
</script>
