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
<script setup lang="ts">
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
  type AxisChartConfig,
  type AxisChartKind,
  type DashboardChartConfig,
  type DonutChartConfig,
  type NumberChartConfig,
  getAxisChartKind,
  toAxisChartProps,
  toDonutChartProps,
  toNumberCardProps,
} from '@/utils/dashboardCharts'
import { computed, type Component } from 'vue'

const props = withDefaults(
  defineProps<{
    index: number
    item: { name?: string; type: string; data?: DashboardChartConfig | null }
    editing?: boolean
  }>(),
  { editing: false },
)

const axisChartComponents: Record<AxisChartKind, Component> = {
  line: LineChart,
  area: AreaChart,
  bar: BarChart,
}

const config = computed<DashboardChartConfig>(() => props.item.data || {})

const numberCardProps = computed(() =>
  toNumberCardProps(config.value as NumberChartConfig),
)
const donutChartProps = computed(() =>
  toDonutChartProps(config.value as DonutChartConfig),
)
const axisChart = computed(() => ({
  component:
    axisChartComponents[getAxisChartKind(config.value as AxisChartConfig)],
  props: toAxisChartProps(config.value as AxisChartConfig),
}))
</script>
