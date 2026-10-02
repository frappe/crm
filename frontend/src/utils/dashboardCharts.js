// Chart resolvers (CRM's and contributed apps') return the experimental config shape; these map it to frappe-ui/charts props.

export function toNumberCardProps(config = {}) {
  const { tooltip, ...props } = config
  return props
}

export function toDonutChartProps(config = {}) {
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
}

export function getAxisChartKind(config = {}) {
  const types = new Set((config.series || []).map((s) => s.type))
  if (types.size === 1 && types.has('line')) return 'line'
  if (types.size === 1 && types.has('area')) return 'area'
  return 'bar'
}

export function toAxisChartProps(config = {}) {
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

  const y2 = series.filter((s) => s.axis === 'y2').map((s) => s.name)

  const valueAxis = (axis) =>
    axis && {
      title: axis.title,
      min: axis.yMin,
      max: axis.yMax,
      echartOptions: axis.echartOptions,
    }

  return {
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
    ...(getAxisChartKind(config) === 'bar' && { horizontal: config.swapXY }),
  }
}
