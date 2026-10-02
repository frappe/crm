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
import { computed } from 'vue'

const props = defineProps({
  index: { type: Number, required: true },
  item: { type: Object, required: true },
  editing: { type: Boolean, default: false },
})

// Chart resolvers (CRM's and contributed apps') return the experimental config shape; map it to frappe-ui/charts props.
const numberCardProps = computed(() => {
  const { tooltip, ...config } = props.item.data || {}
  return config
})

const donutChartProps = computed(() => {
  const config = props.item.data || {}
  return {
    title: config.title,
    subtitle: config.subtitle,
    data: config.data || [],
    category: config.categoryColumn,
    value: config.valueColumn,
    maxSlices: config.maxSliceCount,
    showDataLabels: config.showInlineLabels,
    palette: config.colors,
    echartOptions: config.echartOptions,
  }
})

const axisChart = computed(() => {
  const config = props.item.data || {}
  const series = config.series || []
  const seriesConfig = {}
  series.forEach((s, i) => {
    seriesConfig[s.name] = {
      type: s.type,
      color: s.color || config.colors?.[i],
      showDataLabels: s.showDataLabels,
      showDataPoints: s.showDataPoints,
      dashed: s.lineType === 'dashed' || s.lineType === 'dotted' || undefined,
      stackName: s.stackName,
      echartOptions: s.echartOptions,
    }
  })

  const types = new Set(series.map((s) => s.type))
  const component =
    types.size === 1 && types.has('line')
      ? LineChart
      : types.size === 1 && types.has('area')
        ? AreaChart
        : BarChart

  const y2 = series.filter((s) => s.axis === 'y2').map((s) => s.name)

  const valueAxis = (axis) =>
    axis && {
      title: axis.title,
      min: axis.yMin,
      max: axis.yMax,
      echartOptions: axis.echartOptions,
    }

  return {
    component,
    props: {
      title: config.title,
      subtitle: config.subtitle,
      data: config.data || [],
      x: config.xAxis?.key,
      y: series.filter((s) => s.axis !== 'y2').map((s) => s.name),
      y2: y2.length ? y2 : undefined,
      seriesConfig,
      stacked: config.stacked,
      xAxis: {
        title: config.xAxis?.title,
        type: config.xAxis?.type,
        timeGrain: config.xAxis?.timeGrain,
        echartOptions: config.xAxis?.echartOptions,
      },
      yAxis: valueAxis(config.yAxis),
      y2Axis: valueAxis(config.y2Axis),
      echartOptions: config.echartOptions,
      ...(component === BarChart && { horizontal: config.swapXY }),
    },
  }
})
</script>
